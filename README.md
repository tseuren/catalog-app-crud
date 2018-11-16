# Catalog App with CRUD functionality and Google OAuth2 authentication.
This is a simple CRUD App written in python using the flask framework, an SQLite db with sqlalchemy for ORM and Google OAuth2 for authentication and authorization.

## Setup
- Clone this repo and create an upload folder inside `static/`.

    `git clone https://github.com/tseuren/catalog-app-crud.git`
    `cd catalog-app-crud`
	`mkdir static/uploads`

- Install pipenv to fetch dependencies.

	`pip install --user pipenv`
	`pipenv install`

- Setup database and populate it with some values for testing.

	`pipenv run python db_setup.py`
	`pipenv run python create_db_items.py`

## OAuth2
The application looks for a `client_secret.json` file in the root of the project. Refer to [this](https://developers.google.com/api-client-library/python/auth/web-app) for more information on how to obtain OAuth2 credentials.

## Running the application
Simply run `application.py` in the virtualenv. The webserver will listen on `localhost:8000` by default.

`pipenv run python application.py`

## Dependencies
- flask
- sqlalchemy
- requests
- oauth2client
- bleach
- pillow
