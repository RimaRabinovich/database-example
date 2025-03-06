# Database Example app

A Flask application that uses Google App Engine Datastore to store and manipulate variables.

working app demo: https://database-example-452816.uc.r.appspot.com

## Features

- SET: Set a variable to a specific value
- GET: Retrieve a variable's value
- UNSET: Remove a variable
- NUMEQUALTO: Count variables with a specific value
- UNDO: Revert the most recent command
- REDO: Reapply a previously undone command
- END: Clean up all data

## Used

- Python
- Google App Engine
- Google Cloud Datastore

### Local Development

- Install dependencies: `pip install -r requirements.txt`
- Run app: `python main.py`
- View app at http://127.0.0.1:8080

## Testing

Run `python test_app.py`
