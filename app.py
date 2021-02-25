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
from exceptions import InvalidContactException, DatabaseInsertionException, RegistrationIDsNULLException
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
    tokens = body.get('tokens')
    notification_title = body.get('title')
    notification_body = body.get('body')

    # Check that passed tokens exist in database
    # Such that the api should send notifications to only subscribed tokens
    filtered_tokens = filter_tokens(tokens)
    result = send_notification(filtered_tokens, notification_title, notification_body)
    print(result)

    if isinstance(result, list):
        success = bool(result[0].get('success'))
    else:
        success = bool(result['success'])
    if success:
        # The following database action could be eliminated as the API should not be responsible for db actions
        # Explanation:
        # "handle_notification_storage" function stores the sent notification in database
        # and it creates a relation between the sent notifications and the tokens (as their relation is Many to Many)
        # Another alternative:
        # log the notifications (sender, targeted token, title and body) in a log file for tracking and debugging purposes
        notification_id = handle_notification_storage(notification_title, notification_body, filtered_tokens)
    
    return jsonify({
        'success': success,
        'notification_id': notification_id
    }), 200

# A method that filters passed tokens with the tokens existing in the database
# it returns filtered tokens which are the ones that exist in database 
# and discard the ones that does not exist in database
def filter_tokens(tokens):
    all_existing_tokens_in_db = Token.query.all()
    all_existing_tokens = [_token.token for _token in all_existing_tokens_in_db]
    filtered_tokens = []
    for token in tokens:
        if token in all_existing_tokens:
            filtered_tokens.append(token)
    return filtered_tokens

def send_notification(tokens, notification_title, notification_body):
    push_service = FCMNotification(api_key=api_key)
    if isinstance(tokens, list):
        # if passed registration ids list is empty, raise exception with status code: 400 Bad Request
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
# So the history of notifications and their recipients are maintained 
def store_tokens_notification_relation_in_db(tokens, notification_id):
    for token in tokens:
        token_obj = Token.query.filter_by(token=token).first()
        if token_obj is not None:
            token_notification_entry = TokenNotification(token_id=token_obj.id, notification_id=notification_id)
            token_notification_entry.insert()

@app.route('/notifications/topic', methods=['POST'])
def send_notification_to_topic():
    body = request.get_json()
    topic_name = body.get('topic')
    message_body = body.get('body')
    message_title = body.get('title')
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
        'message': "Registration IDs cannot be nulled list"
    }), error.status_code

if __name__ == "__main__":
    app.run('0.0.0.0', '5000', debug=True)