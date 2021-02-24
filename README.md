# flask-sms-notifications-app
Flask based backend application that implement endpoints that can send SMSs (needs to integrate with real service provider first) and can notifications via FCM (Firebase Cloud Messaging) to registered users.
The application integrates with a postgres database that keep records of the sent messages and notifications for tracking and history purposes.

## Pre-requisites to run the project
1. install [Python](https://www.python.org/downloads/release) latest version
2. install [Postgres](https://www.postgresql.org/download/) software according to your OS
3. Clone the project's repo and you are ready!

##### Key Dependencies
- [Flask](http://flask.pocoo.org/) is a lightweight backend microservices framework. Flask is required to handle requests and responses.
- [SQLAlchemy](https://www.sqlalchemy.org/) is the Python SQL toolkit and ORM we'll use handle the lightweight postgres database.

## Steps to prepare the project's environment
1. Navigate to the project's directory and install all project's dependencies by running this command at the CMD/terminal:
```bash
pip install -r requirements.txt
```
2. Setup the database by creating a Postgres database
```bash
createdb database_name
 ```
3. Open `models.py` to configure the following with your inputs:
    - database_name
    - user
    - password
4. Migrate database using database migrations, using flask migrate
   but first you have to set the flask app in the environment variable "FLASK_APP" as following:
```bash
set FLASK_APP=app.py
```
  then run the flask migrate commands as following:
```bash
flask db init
flask db migrate
flask db upgrade
```
5. Import the database data included in the project's directory, so you can have some initial data in your created postgres database
```bash
psql database_name < database_file.psql
```

## Steps to run the project's app
1. In CMD/terminal, type the following:
```bash
set FLASK_APP=app.py
flask run --reload
```
or simply
```bash
python app.py
```
Application runs on 'http://127.0.0.1:5000/' or 'localhost:5000'

2. When you open the localhost root page `/` an empty HTML page shall be rendered and it will contain the device registration token
3. This token shall be used to send notifications to the page, so save it in an external file for later usage

Important Note:
* If the root page remained static and no token appeared, you have to the localhost on "https"
* You can use a free software [ngrok](https://ngrok.com/) to achieve this, it is pretty simple and neat!

## APIs Documentation
### Getting Started
In order to execute and test the API endpoints, you can user either [Postman](https://www.postman.com/downloads/) or Curl commands
- Base URL: At present this app can only be run locally and is not hosted as a base URL. 
- The backend app runs at `http://127.0.0.1:5000/`
- Authentication: This version of the application does not require authentication.
- Connect to Postgres Database by configuring the Database name, Username and Password at `models.py`

### Error Handling
HTTP Errors are returned as JSON objects in the following format:
```bash
{
    "success": False,
    "error": 404,
    "message": "Not Found"
}
```
The APIs will handle all types of HTTP errors when requests fail or request data cannot be found or something went wrong for any reason

### Endpoints Library

```bash
POST '/send-sms'
POST '/send-notification'
POST '/notify-topic'
```

#### POST '/send-sms'
- Send SMS to a single contact number, it needs to be integrate with real SMS service provider
- Sending SMS requests are limited per minute
- Request Arguments: 'contact', 'subject', 'message'
- 'contact' have to be correctly formated "[+country_code].*[number]"
- Returns: JSON Object contains 'success', 'message_id'
- Sample: `curl http://127.0.0.1:5000/send-sms -X POST -H "Content-Type: application/json" -d "{"contact": "+201009129288", "subject": "SMS Subject", "message": "This is a message body"}"`
```bash
    {
      "message_id": 1,
      "success": true
    }
```

#### POST '/send-notification'
- Send notification to subscribed tokens using FCM (Firebase Cloud Messaging) under the hood
- Request Arguments: 'tokens', 'title', 'body'
- 'tokens' is a list of subscribed token which the notification shall be sent to, tokens have to be valid and correctly formated. 
- You can retrieve a token by running the root route of the application "http://127.0.0.1:5000", copy and paste the generated token
- Returns: JSON Object contains 'success', 'notification_id'
- Sample: `curl http://127.0.0.1:5000/send-notification -X POST -H "Content-Type: application/json" -d "{"tokens": ["dyimeAKczeP3UJ8ynvI1I2:APA91bHQFAK2d28Tyfg89zqWVrPynCCEXF9eNnRW705fFxEdDE4klEBsqlVsdWiXl3jkWykCQ503Nh4m6EeL3tNS7iR1mnCB9e_Q7Sw_wDd_N3nENiqwmpTV2e1blahBck03zhR9t4LJ"], "title": "Notification Title", "body": "This is a notification body"}"`
```bash
    {
      "notification_id": 1,
      "success": true
    }
```

#### POST '/notify-topic'
- Send notification to users subscribing to specific topic
- Request Arguments: 'topic', 'title', 'body'
- Returns: JSON Object contains 'success'
- Sample: `curl http://127.0.0.1:5000/send-sms -X POST -H "Content-Type: application/json" -d "{"topic": "news", "title": "Notification Title", "body": "This is a topic notification body"}"`
```bash
    {
      "success": true
    }
```

## Testing
The project files contain file `app_test.py`, this file contains all the unit tests that test the API endpoints
To run the tests, open CMD terminal and execute the following (make sure that the server is up and running)
```bash
python test_app.py
```
Test cases will be executed and result will be displayed in the CMD terminal incase of success or failure

## Authors
Software Engineer/ Yousif Elhady
