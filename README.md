# flask-sms-notifications-app
Flask based backend application that implements endpoints that can send SMSs (needs to be integrated with real service provider) and can send notifications via FCM (Firebase Cloud Messaging) to registered users.
The application integrates with a postgres database that keep records of the sent messages and notifications for tracking and history purposes.
The whole project can run and execute using Docker-Compose.

## Docker-Compose Setup
1. Download [Docker](https://www.docker.com/) at your machine in order to be able to execute docker commands.
2. Clone the project repo.
3. Run CMD terminal from the project's directory and execute:
```bash
docker-compose up
```
4. Docker will setup the project's environement, install all the dependencies and handle the database connection.
5. Jump to "API Documentation" section to start using and testing the endpoints.
<br>

## Pre-requisites to run the project
1. install [Python](https://www.python.org/downloads/release) latest version
2. install [Postgres](https://www.postgresql.org/download/) software according to your OS
3. Clone the project's repo and you are ready!

##### Key Dependencies
- [Flask](http://flask.pocoo.org/) is a lightweight backend microservices framework. Flask is required to handle requests and responses.
- [SQLAlchemy](https://www.sqlalchemy.org/) is the Python SQL toolkit and ORM we'll use handle the lightweight postgres database.
- [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/) is a flask library used to handle db migrations.
- [PyFCM](https://pypi.org/project/pyfcm/) is a python library that wraps the FCM functionalities of Google Firebase

## Steps to prepare the project's environment
1. Navigate to the project's directory and firstly create a virtual python environment to install the project's dependencies. <br>
Follow the steps of how to configure a virtual environment from [here](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
2. Activate the virtual environment by running `activate.bat` from (./env/Scripts)
3. Install all the project's dependencies by running this command at the CMD/terminal:
```bash
pip install -r requirements.txt
```
4. Setup the database by creating a local Postgres database
Postgres default username/password: postgres/postgres
```bash
createdb database_name
 ```
5. Open `models.py` to configure the following with your inputs:
    - database_name
    - user
    - password
    - localhost (default: localhost)
6. You can skip (no.5) and configure the values using environment variables corresponding to their names in the `models.py` file.
7. Migrate database using database migrations using flask migrate,
   but first you have to set the flask app in the environment variable "FLASK_APP" as following:
```bash
set FLASK_APP=app.py
```
   then run the flask migrate commands as following:
```bash
flask db upgrade
```
   hence, database tables shall be created (they will be initially empty). <br><br>
8. To verify that the database tables have been created, type the following in the CMD terminal:
```bash
psql database_name
```
you will enter the command line mode of postgres database, then type:
```bash
\dt
```

## Steps to run the project's app
1. In CMD/terminal, type the following:
```bash
set FLASK_APP=app.py
flask run --reload
```
Applcation will run on `http://127.0.0.1:5000/` <br><br>
or just execute the app file
```bash
python app.py
```
Application will run on the specified url in "app.py" which is `http://0.0.0.0:5000/` and to run it, use `http://localhost:5000`

2. When you open the localhost root page `/` an empty HTML page shall be rendered and it will contain the device registration token.
3. This token shall be used to send notifications to the page, so save it in an external file for later usage.

Important Note:
* If the root page remained static and no token appeared, you have to run the localhost on "https".
* You can use a free software [ngrok](https://ngrok.com/) to achieve this, it is pretty simple and neat!

## APIs Documentation
### Getting Started
In order to execute and test the API endpoints, you can use either [Postman](https://www.postman.com/downloads/) or Curl commands.
- Base URL: At present this app can only be run locally and is not hosted as a base URL. 
- The backend app runs at `http://localhost:5000`
- Authentication: This version of the application does not require authentication.
- Make sure to connect to the Postgres database by configuring its login data at `models.py`

### Error Handling
HTTP Errors are returned as JSON objects in the following format:
```bash
{
    "success": False,
    "error": 404,
    "message": "Not Found"
}
```
The APIs will handle all types of HTTP errors when requests fail or request data cannot be found or something went wrong for any reason.

### Endpoints Library

```bash
POST '/smss'
POST '/notifications/tokens'
POST '/notifications/topic'
```

#### POST '/smss'
- Send SMS to a single contact number, it needs to be integrate with real SMS service provider.
- Sending SMS requests are limited per minute.
- Request Arguments: 'contact', 'subject', 'message'
- 'contact' have to be correctly formated "[+country_code].*[number]"
- Returns: JSON Object contains 'success', 'message_id'
- Sample: `curl http://localhost:5000/smss -X POST -H "Content-Type: application/json" -d "{"contact": "+201009129288", "subject": "SMS Subject", "message": "This is a message body"}"`
```bash
    {
      "message_id": 1,
      "success": true
    }
```

#### POST '/notifications/tokens'
- Send notification to subscribed tokens using FCM (Firebase Cloud Messaging) under the hood.
- Request Arguments: 'tokens', 'title', 'body'
- 'tokens' is a list of subscribed tokens to which the notification shall be sent, tokens have to be valid and correctly formated.
- You can retrieve a token by running the root route of the application "http://localhost:5000", copy and paste the generated token to Postman or Curl as shown in the sample bellow.
- Returns: JSON Object contains 'success', 'notification_id'
- Sample: `curl http://localhost:5000/notifications/tokens -X POST -H "Content-Type: application/json" -d "{"tokens": ["dyimeAKczeP3UJ8ynvI1I2:APA91bHQFAK2d28Tyfg89zqWVrPynCCEXF9eNnRW705fFxEdDE4klEBsqlVsdWiXl3jkWykCQ503Nh4m6EeL3tNS7iR1mnCB9e_Q7Sw_wDd_N3nENiqwmpTV2e1blahBck03zhR9t4LJ"], "title": "Notification Title", "body": "This is a notification body"}"`
```bash
    {
      "notification_id": 1,
      "success": true
    }
```

#### POST '/notifications/topic'
- Send notification to users who are subscribing to a specific topic.
- The Notification will be sent anyway and users who are subscribing to the topic shall receive it.
- Request Arguments: 'topic', 'title', 'body'
- Returns: JSON Object contains 'success'
- Sample: `curl http://localhost:5000/notifications/topic -X POST -H "Content-Type: application/json" -d "{"topic": "news", "title": "Notification Title", "body": "This is a topic notification body"}"`
```bash
    {
      "success": true
    }
```

## Testing
The project files contain a file `app_test.py`, this file contains all the unit tests that test the API endpoints
To run the tests, open CMD terminal and execute the following (make sure that the server is up and running)
```bash
python test_app.py
```
Test cases will be executed and result will be displayed in the CMD terminal incase of success or failure.

## Acknowledgement
I would like to acknowledge Software Engineer/ [Hussein Khaled](https://github.com/husseinkk) for his contribution and help in setting up Docker-compose for the project.

## Authors
Software Engineer/ Yousif Elhady
