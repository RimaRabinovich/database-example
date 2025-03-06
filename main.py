from flask import Flask, request, render_template
from google.cloud import datastore
import uuid
import datetime

app = Flask(__name__)
datastore_client = datastore.Client()

# kinds for datastore
VARIABLE_KIND = 'Variable'
COMMAND_KIND = 'Command'
METADATA_KIND = 'Metadata'
VALUE_COUNT_KIND = 'ValueCount'

# pointers to track command history for undo/redo
def ensure_metadata_exists():
    key = datastore_client.key(METADATA_KIND, 'command_pointers')
    entity = datastore_client.get(key)
    if not entity:
        entity = datastore.Entity(key=key)
        entity.update({
            'current_pointer': -1,
            'max_pointer': -1
        })
        datastore_client.put(entity)
    return entity

# record command for undo/redo functionality
def record_command(command_type, name=None, old_value=None, new_value=None):
    with datastore_client.transaction():
        # get pointers
        metadata = ensure_metadata_exists()
        current_pointer = metadata['current_pointer']
        
        # if not at end of command history, delete all future commands
        if current_pointer < metadata['max_pointer']:
            # delete all commands after current_pointer
            query = datastore_client.query(kind=COMMAND_KIND)
            query.add_filter('index', '>', current_pointer)
            commands_to_delete = list(query.fetch())
            keys_to_delete = [cmd.key for cmd in commands_to_delete]
            if keys_to_delete:
                datastore_client.delete_multi(keys_to_delete)
        
        # create new command
        command_id = str(uuid.uuid4())
        key = datastore_client.key(COMMAND_KIND, command_id)
        entity = datastore.Entity(key=key)
        
        # increment pointers
        new_index = current_pointer + 1
        
        entity.update({
            'index': new_index,
            'type': command_type,
            'name': name,
            'old_value': old_value,
            'new_value': new_value,
            'timestamp': datetime.datetime.now()
        })
        
        # update metadata
        metadata.update({
            'current_pointer': new_index,
            'max_pointer': new_index
        })
        
        # save entities
        datastore_client.put_multi([entity, metadata])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set')
def set_variable():
    # get name and value from request
    name = request.args.get('name')
    value = request.args.get('value')
    
    if not name or not value:
        return "Error: Both name and value parameters are required", 400
    
    with datastore_client.transaction():
        # create key
        key = datastore_client.key(VARIABLE_KIND, name)
        
        # check if already exists to record old value
        old_entity = datastore_client.get(key)
        old_value = old_entity['value'] if old_entity and 'value' in old_entity else None
        
        # update value counts kind
        if old_value:
            # decrement count for old value
            old_count_key = datastore_client.key(VALUE_COUNT_KIND, old_value)
            old_count_entity = datastore_client.get(old_count_key)
            if old_count_entity and old_count_entity['count'] > 1:
                old_count_entity.update({'count': old_count_entity['count'] - 1})
                datastore_client.put(old_count_entity)
            elif old_count_entity:
                datastore_client.delete(old_count_key)
        
        # increment count for new value
        new_count_key = datastore_client.key(VALUE_COUNT_KIND, value)
        new_count_entity = datastore_client.get(new_count_key)
        if new_count_entity:
            new_count_entity.update({'count': new_count_entity['count'] + 1})
        else:
            new_count_entity = datastore.Entity(key=new_count_key)
            new_count_entity.update({'count': 1})
        datastore_client.put(new_count_entity)
        
        # create variable
        entity = datastore.Entity(key=key)
        entity.update({
            'value': value
        })
        
        # save to datastore
        datastore_client.put(entity)
        
        # record command for undo/redo
        record_command('SET', name, old_value, value)
    
    return f"{name} = {value}"

@app.route('/get')
def get_variable():
    # get name from request
    name = request.args.get('name')
    
    if not name:
        return "Error: Name parameter is required", 400
    
    # create key
    key = datastore_client.key(VARIABLE_KIND, name)
    
    # get entity from datastore
    entity = datastore_client.get(key)
    
    if entity and 'value' in entity:
        return entity['value']
    else:
        return "None"

@app.route('/unset')
def unset_variable():
    # get name from request
    name = request.args.get('name')
    
    if not name:
        return "Error: Name parameter is required", 400
    
    with datastore_client.transaction():
        # create key
        key = datastore_client.key(VARIABLE_KIND, name)
        
        # get current value for undo
        entity = datastore_client.get(key)
        old_value = entity['value'] if entity and 'value' in entity else None
        
        if old_value:
            # decrement count for old value
            count_key = datastore_client.key(VALUE_COUNT_KIND, old_value)
            count_entity = datastore_client.get(count_key)
            if count_entity and count_entity['count'] > 1:
                count_entity.update({'count': count_entity['count'] - 1})
                datastore_client.put(count_entity)
            elif count_entity:
                datastore_client.delete(count_key)
        
        # delete from datastore
        datastore_client.delete(key)
        
        # record command for undo/redo
        record_command('UNSET', name, old_value, None)
    
    return f"{name} = None"

@app.route('/numequalto')
def num_equal_to():
    # get value from request
    value = request.args.get('value')
    
    if not value:
        return "Error: Value parameter is required", 400
    
    # get count directly O(1)
    count_key = datastore_client.key(VALUE_COUNT_KIND, value)
    count_entity = datastore_client.get(count_key)
    
    if count_entity and 'count' in count_entity:
        return str(count_entity['count'])
    else:
        return "0"

@app.route('/undo')
def undo():
    # get current pointers
    metadata = ensure_metadata_exists()
    current_pointer = metadata['current_pointer']
    
    if current_pointer < 0:
        return "NO COMMANDS"
    
    # get command to undo
    query = datastore_client.query(kind=COMMAND_KIND)
    query.add_filter('index', '=', current_pointer)
    commands = list(query.fetch(limit=1))
    
    if not commands:
        return "NO COMMANDS"
    
    command = commands[0]
    name = command['name']
    
    with datastore_client.transaction():
        # perform undo based on command type
        if command['type'] == 'SET':
            # update value counts
            if command['new_value']:
                # decrement count for current value
                current_count_key = datastore_client.key(VALUE_COUNT_KIND, command['new_value'])
                current_count_entity = datastore_client.get(current_count_key)
                if current_count_entity and current_count_entity['count'] > 1:
                    current_count_entity.update({'count': current_count_entity['count'] - 1})
                    datastore_client.put(current_count_entity)
                elif current_count_entity:
                    datastore_client.delete(current_count_key)
            
            if command['old_value'] is None:
                # it was a new variable, so unset it
                key = datastore_client.key(VARIABLE_KIND, name)
                datastore_client.delete(key)
                result = f"{name} = None"
            else:
                # restore old value and increment its count
                key = datastore_client.key(VARIABLE_KIND, name)
                entity = datastore.Entity(key=key)
                entity.update({
                    'value': command['old_value']
                })
                datastore_client.put(entity)
                
                # increment count for old value
                old_count_key = datastore_client.key(VALUE_COUNT_KIND, command['old_value'])
                old_count_entity = datastore_client.get(old_count_key)
                if old_count_entity:
                    old_count_entity.update({'count': old_count_entity['count'] + 1})
                else:
                    old_count_entity = datastore.Entity(key=old_count_key)
                    old_count_entity.update({'count': 1})
                datastore_client.put(old_count_entity)
                
                result = f"{name} = {command['old_value']}"
        elif command['type'] == 'UNSET':
            # restore variable and increment its count
            key = datastore_client.key(VARIABLE_KIND, name)
            entity = datastore.Entity(key=key)
            entity.update({
                'value': command['old_value']
            })
            datastore_client.put(entity)
            
            # increment count for old value
            old_count_key = datastore_client.key(VALUE_COUNT_KIND, command['old_value'])
            old_count_entity = datastore_client.get(old_count_key)
            if old_count_entity:
                old_count_entity.update({'count': old_count_entity['count'] + 1})
            else:
                old_count_entity = datastore.Entity(key=old_count_key)
                old_count_entity.update({'count': 1})
            datastore_client.put(old_count_entity)
            
            result = f"{name} = {command['old_value']}"
        
        # update pointer
        metadata.update({
            'current_pointer': current_pointer - 1
        })
        datastore_client.put(metadata)
    
    return result

@app.route('/redo')
def redo():
    # get pointers
    metadata = ensure_metadata_exists()
    current_pointer = metadata['current_pointer']
    max_pointer = metadata['max_pointer']
    
    if current_pointer >= max_pointer:
        return "NO COMMANDS"
    
    # get command to redo
    next_pointer = current_pointer + 1
    query = datastore_client.query(kind=COMMAND_KIND)
    query.add_filter('index', '=', next_pointer)
    commands = list(query.fetch(limit=1))
    
    if not commands:
        return "NO COMMANDS"
    
    command = commands[0]
    name = command['name']
    
    with datastore_client.transaction():
        # perform redo based on command type
        if command['type'] == 'SET':
            # check if variable exists
            key = datastore_client.key(VARIABLE_KIND, name)
            existing_entity = datastore_client.get(key)
            existing_value = existing_entity['value'] if existing_entity and 'value' in existing_entity else None
            
            # update value counts, if it exists decrement count
            if existing_value:
                existing_count_key = datastore_client.key(VALUE_COUNT_KIND, existing_value)
                existing_count_entity = datastore_client.get(existing_count_key)
                if existing_count_entity and existing_count_entity['count'] > 1:
                    existing_count_entity.update({'count': existing_count_entity['count'] - 1})
                    datastore_client.put(existing_count_entity)
                elif existing_count_entity:
                    datastore_client.delete(existing_count_key)
            
            # increment count for new value
            new_value = command['new_value']
            new_count_key = datastore_client.key(VALUE_COUNT_KIND, new_value)
            new_count_entity = datastore_client.get(new_count_key)
            if new_count_entity:
                new_count_entity.update({'count': new_count_entity['count'] + 1})
            else:
                new_count_entity = datastore.Entity(key=new_count_key)
                new_count_entity.update({'count': 1})
            datastore_client.put(new_count_entity)
            
            # update variable
            entity = datastore.Entity(key=key)
            entity.update({
                'value': new_value
            })
            datastore_client.put(entity)
            result = f"{name} = {new_value}"
            
        elif command['type'] == 'UNSET':
            # get value to decrement count
            key = datastore_client.key(VARIABLE_KIND, name)
            existing_entity = datastore_client.get(key)
            existing_value = existing_entity['value'] if existing_entity and 'value' in existing_entity else None
            
            if existing_value:
                # decrement count for value removed
                count_key = datastore_client.key(VALUE_COUNT_KIND, existing_value)
                count_entity = datastore_client.get(count_key)
                if count_entity and count_entity['count'] > 1:
                    count_entity.update({'count': count_entity['count'] - 1})
                    datastore_client.put(count_entity)
                elif count_entity:
                    datastore_client.delete(count_key)
            
            # delete variable
            datastore_client.delete(key)
            result = f"{name} = None"
        
        # update pointer
        metadata.update({
            'current_pointer': next_pointer
        })
        datastore_client.put(metadata)
    
    return result

@app.route('/end')
def end_program():
    # Delete all variables
    query = datastore_client.query(kind=VARIABLE_KIND)
    variables = list(query.fetch())
    keys_to_delete = [var.key for var in variables]
    
    # Delete all commands
    query = datastore_client.query(kind=COMMAND_KIND)
    commands = list(query.fetch())
    keys_to_delete.extend([cmd.key for cmd in commands])
    
    # Delete metadata
    query = datastore_client.query(kind=METADATA_KIND)
    metadata = list(query.fetch())
    keys_to_delete.extend([meta.key for meta in metadata])
    
    # Delete value counts
    query = datastore_client.query(kind=VALUE_COUNT_KIND)
    value_counts = list(query.fetch())
    keys_to_delete.extend([count.key for count in value_counts])
    
    # Delete everything
    if keys_to_delete:
        datastore_client.delete_multi(keys_to_delete)
    
    return "CLEANED"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
