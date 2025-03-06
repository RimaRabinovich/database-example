# Database Example app

A Flask application that uses Google App Engine Datastore to store and manipulate variables.

working app demo: https://database-example-452816.uc.r.appspot.com

<img width="928" alt="Screenshot 2025-03-06 at 13 51 13" src="https://github.com/user-attachments/assets/6e7b678e-2dd7-4e3e-be41-43b446a91553" />

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
