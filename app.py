from flask import Flask, request, jsonify, abort, render_template, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os
import pathlib
from werkzeug.exceptions import HTTPException
from datetime import datetime
import re
from pyfcm import FCMNotification

from models import Client, Message, Notification, Token, TokenNotification, setup_db
from exceptions import InvalidContactException, DatabaseInsertionException, RegistrationIDsNULLException

# Constants region
contact_fixed_length = 13
api_key = 'AAAA6EwhWKo:APA91bHJiaWrXskFxQGQoybatbMLJxiDBC7nDT5hu7w8YYT1q_tZ2lnWqLjZeMpgPHjGYexZWiRhoq3ibxAUtkdyRLuIeripcVVi4-PzrvW2GcKJkWpbRCzSzd4NenMR8dGGSP931AUk'
##################

def create_app():
    app = Flask(__name__)
    setup_db(app)
    CORS(app)
    return app

# Initializing app
app = create_app()
limiter = Limiter(app, key_func=get_remote_address)
##################

@app.route('/<path:path>')
def send_js_path(path):
    return send_from_directory('.', path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send-sms', methods=['POST'])
@limiter.limit('3 per minute')
# external config file can be used to configure the limit dynamically without being hardcoded
def send_sms():
    body = request.get_json()
    client_id = body.get('id')
    client = Client.query.get(client_id)
    if client is None:
        abort(404)
    
    client_contact = client.contact
    if not is_valid_contact_format(client_contact):
        #if contact is not valid, raise exception with status code: 400 Bad Request
        raise InvalidContactException(client_contact, 400)
    
    client_name = client.name
    if not client_name:
        client_name = ""
    subject = body.get('subject')
    # applying some message decorating
    message = f'Dear Mr/Mrs ' + str(client_name) + ', '
    message += body.get('message')
    
    send_sms_to_client(client_contact, subject, message)
    store_message_in_db(subject, message, client_id)
    #return frontend expected JSON
    return jsonify({
        'success': True,
        'client_id': client_id,
        'message': message
    }), 200

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

def send_sms_to_client(client_contact, subject, message):
    #integrate with real sms provider
    #example: callr or twillo
    #api = callr.Api('valeo_1', 'yousifelhady.1994')
    #testSMS = api.call('sms.send', subject, client_contact, message, None)
    print('message subject: ' + subject)
    print('message body: ' + message)
    print('has been sent to: ' + client_contact)

def store_message_in_db(subject, message, client_id):
    current_time = datetime.now()
    new_message = Message(subject=subject, body=message, time=current_time, client_id=client_id)
    new_message.insert()

@app.route('/send-notification', methods=['POST'])
def send_notification():
    push_service = FCMNotification(api_key=api_key)
    body = request.get_json()
    registration_ids = body.get('tokens')
    notification_title = body.get('title')
    notification_body = body.get('body')
    
    result = send_notification_to_devices(push_service, registration_ids, notification_title, notification_body)
    print(result)
    if isinstance(result, list):
        success = bool(result[0].get('success'))
    else:
        success = bool(result['success'])
    if success:
        # The following database action could be eliminated as the API is not responsible for db actions
        # Explanation:
        # "handle_database_actions" function stores the passed tokens and the sent notification in database
        # and it store the relation between them in third table (as their relation is Many to Many)
        # Another alternatives:
        # 1. use firestore db to store tokens and sent notifications
        # 2. use mongodb as nosql db
        # 3. log the notifications (sender, targeted token, title and body) in a log file for tracking and debugging purposes
        handle_database_actions(notification_title, notification_body, registration_ids)
    return jsonify({
        'success': success,
        'tokens': registration_ids,
        'title': notification_title,
        'body': notification_body
    }), 200

def send_notification_to_devices(push_service, registration_ids, notification_title, notification_body):
    if isinstance(registration_ids, list):
        # if passed registration ids list is empty, raise exception with status code: 400 Bad Request
        if registration_ids == []:
            raise RegistrationIDsNULLException(status_code=400)
        return push_service.notify_multiple_devices(registration_ids=registration_ids, message_body=notification_body, message_title=notification_title)
    else:
        return push_service.notify_single_device(registration_id=registration_ids, message_body=notification_body, message_title=notification_title)

def handle_database_actions(title, body, registration_ids):
    notification_id = store_notification_in_db(title, body)
    store_tokens_notification_relation_in_db(registration_ids, notification_id)

def store_notification_in_db(title, body):
    current_time = datetime.now()
    newNotification = Notification(title=title, body=body, time=current_time)
    newNotification.insert()
    newNotification_id = newNotification.id
    return newNotification_id
    
def store_tokens_notification_relation_in_db(registration_ids, notification_id):
    stored_tokens = Token.query.all()
    stored_tokens = [_token.token for _token in stored_tokens]
    for reg_id in registration_ids:
        if reg_id not in stored_tokens:
            newToken = Token(token=reg_id)
            newToken.insert()
            token_id = newToken.id
        else:
            existing_token = Token.query.filter_by(token=reg_id).first()
            token_id = existing_token.id
        token_notification_entry = TokenNotification(token_id=token_id, notification_id=notification_id)
        token_notification_entry.insert()

@app.route('/notify-topic', methods=['POST'])
def notify_topic():
    push_service = FCMNotification(api_key=api_key)
    body = request.get_json()
    topic_name = body.get('topic')
    message_body = body.get('body')
    message_title = body.get('title')
    result = push_service.notify_topic_subscribers(topic_name=topic_name, message_body=message_body, message_title=message_title)
    print(result)
    success = bool(result['success'])
    if success:
        status_code = 200
    else:
        status_code = 500
    return jsonify({
        'success': success
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
    app.run('127.0.0.1', '5000', debug=True)