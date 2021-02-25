from flask import Flask, request, jsonify, abort, render_template, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os
from werkzeug.exceptions import HTTPException
from datetime import datetime
import re
from pyfcm import FCMNotification

from models import Client, Message, Notification, Token, TokenNotification, setup_db
from exceptions import InvalidContactException, DatabaseInsertionException, RegistrationIDsNULLException, JSONBodyFormatException, MissingJSONBodyException
from config import api_key, api_limit_per_minute

# Constants region
contact_fixed_length = 13
api_key = api_key
##################

def initialize_app():
    app = Flask(__name__)
    setup_db(app)
    CORS(app)
    return app

# Initializing app
app = initialize_app()
limiter = Limiter(app, key_func=get_remote_address)
##################

@app.route('/<path:path>')
def send_js_path(path):
    return send_from_directory('.', path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/smss', methods=['POST'])
@limiter.limit(str(api_limit_per_minute) + '/minute')
def send_sms():
    body = request.get_json()
    if not body:
        raise MissingJSONBodyException(status_code=400)
    if 'contact' not in body or 'subject' not in body or 'message' not in body:
        raise JSONBodyFormatException(status_code=400)

    contact = body.get('contact')
    subject = body.get('subject')
    message = body.get('message')

    if not is_valid_contact_format(contact):
        #if contact is not valid, raise exception with status code: 400 Bad Request
        raise InvalidContactException(contact, 400)
    
    send_sms_to_contact(contact, subject, message)
    # Retrieve client object from database (if exist)
    client = Client.query.filter_by(contact=contact).first()
    if client is None:
        # If client does not exist in database, create a record for it
        client_id = store_client_in_db(contact)
    else:
        client_id = client.id
    new_message_id = store_message_in_db(subject, message, client_id)
    #return frontend expected JSON
    return jsonify({
        'success': True,
        'message_id': new_message_id
    }), 200

# Validate the passed contact with respect to its country code and its format
def is_valid_contact_format(client_contact):
    # check that the contact starts with '+20' which is Egypt's country code 
    # and end with number
    # example: +201009129288
    is_valid_format = re.search("[\'+20\'].+[0123456789]$", client_contact)
    #check that the contact is all numeric
    is_valid_contact = client_contact[1:len(client_contact)].isnumeric()
    #check that the contact contains 13 character ('+' sign and 12 numeric)
    is_valid_contact_len = len(client_contact) == contact_fixed_length
    return is_valid_format and is_valid_contact and is_valid_contact_len

def store_client_in_db(contact):
    newClient = Client(contact=contact)
    newClient.insert()
    return newClient.id

def send_sms_to_contact(contact, subject, message):
    #integrate with real sms provider
    #example: callr or twillo
    #api = callr.Api('valeo_1', 'yousifelhady.1994')
    #testSMS = api.call('sms.send', subject, contact, message, None)
    print('message subject: ' + subject)
    print('message body: ' + message)
    print('has been sent to: ' + contact)

def store_message_in_db(subject, message, client_id):
    current_time = datetime.now()
    new_message = Message(subject=subject, body=message, time=current_time, client_id=client_id)
    new_message.insert()
    return new_message.id

@app.route('/notifications/tokens', methods=['POST'])
def send_notification_to_tokens():
    body = request.get_json()
    if not body:
        raise MissingJSONBodyException(status_code=400)
    if 'tokens' not in body or 'title' not in body or 'body' not in body:
        raise JSONBodyFormatException(status_code=400)

    tokens = body.get('tokens')
    notification_title = body.get('title')
    notification_body = body.get('body')

    result = send_notification(tokens, notification_title, notification_body)
    print(result)

    if isinstance(result, list):
        success = bool(result[0].get('success'))
    else:
        success = bool(result['success'])
    if success:
        # The following database action could be remove (if not required) as the API should not be responsible for db actions
        # Explanation:
        # "handle_notification_storage" function stores the sent notification and targeted tokens in database
        # and it creates a relation between the sent notification and the tokens (as their relation is Many to Many)
        # Another alternative:
        # log the notification's (sender, targeted token, title and body) in a log file for tracking and debugging purposes
        notification_id = handle_notification_storage(notification_title, notification_body, tokens)
    
    return jsonify({
        'success': success,
        'notification_id': notification_id
    }), 200

def send_notification(tokens, notification_title, notification_body):
    push_service = FCMNotification(api_key=api_key)
    if isinstance(tokens, list):
        # if passed tokens list is empty, raise exception with status code: 400 Bad Request
        if tokens == []:
            raise RegistrationIDsNULLException(status_code=400)
        return push_service.notify_multiple_devices(registration_ids=tokens, message_body=notification_body, message_title=notification_title)
    else:
        return push_service.notify_single_device(registration_id=tokens, message_body=notification_body, message_title=notification_title)

def handle_notification_storage(title, body, tokens):
    notification_id = store_notification_in_db(title, body)
    store_tokens_notification_relation_in_db(tokens, notification_id)
    return notification_id

def store_notification_in_db(title, body):
    current_time = datetime.now()
    newNotification = Notification(title=title, body=body, time=current_time)
    newNotification.insert()
    return newNotification.id

# Store a relation between the sent notification id and targeted tokens ids
# So the history of notifications and their recipients are maintained.
# If tokens are not existing in database, they will be stored too
def store_tokens_notification_relation_in_db(tokens, notification_id):
    stored_tokens = Token.query.all()
    stored_tokens = [_token.token for _token in stored_tokens]
    for token in tokens:
        if token not in stored_tokens:
            newToken = Token(token=token)
            newToken.insert()
            token_id = newToken.id
        else:
            existing_token = Token.query.filter_by(token=token).first()
            token_id = existing_token.id
        token_notification_entry = TokenNotification(token_id=token_id, notification_id=notification_id)
        token_notification_entry.insert()

@app.route('/notifications/topic', methods=['POST'])
def send_notification_to_topic():
    body = request.get_json()
    if not body:
        raise MissingJSONBodyException(status_code=400)
    if 'topic' not in body or 'title' not in body or 'body' not in body:
        raise JSONBodyFormatException(status_code=400)
    
    topic_name = body.get('topic')
    message_title = body.get('title')
    message_body = body.get('body')
    
    push_service = FCMNotification(api_key=api_key)
    result = push_service.notify_topic_subscribers(topic_name=topic_name, message_body=message_body, message_title=message_title)
    print(result)
    success = bool(result['success'])
    if success:
        status_code = 200
    else:
        status_code = 500
    return jsonify({
        'success': success,
    }), status_code

@app.errorhandler(HTTPException)
def handle_HTTPException(error):
    return jsonify({
        "success": False, 
        "error": error.code,
        "message": error.name
        }), error.code

@app.errorhandler(InvalidContactException)
def handle_InvalidContactException(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': "Invalid contact: " + error.contact
    }), error.status_code

@app.errorhandler(DatabaseInsertionException)
def handle_DatabaseInsertionException(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': "Error occured while inserting in database: " + error.exception_message
    }), error.status_code

@app.errorhandler(RegistrationIDsNULLException)
def hande_RegistrationIDsNULLException(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': "Tokens list cannot be empty / nulled list"
    }), error.status_code

@app.errorhandler(JSONBodyFormatException)
def hande_JSONBodyFormatException(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': "Passed JSON body format is incorrect"
    }), error.status_code

@app.errorhandler(MissingJSONBodyException)
def hande_MissingJSONBodyException(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': "Method cannot have empty JSON body"
    }), error.status_code

if __name__ == "__main__":
    app.run('0.0.0.0', '5000', debug=True)