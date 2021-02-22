from flask import Flask, request, jsonify, abort, render_template, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import pathlib
from werkzeug.exceptions import HTTPException
from datetime import datetime
import re
from pyfcm import FCMNotification

from models import Client, Message, Notification, setup_db
from exceptions import InvalidContactException, DatabaseInsertionException, RegistrationIDsNULLException

app = Flask(__name__)
setup_db(app)
limiter = Limiter(app, key_func=get_remote_address)
contact_fixed_length = 13
api_key = 'AAAA6EwhWKo:APA91bHJiaWrXskFxQGQoybatbMLJxiDBC7nDT5hu7w8YYT1q_tZ2lnWqLjZeMpgPHjGYexZWiRhoq3ibxAUtkdyRLuIeripcVVi4-PzrvW2GcKJkWpbRCzSzd4NenMR8dGGSP931AUk'

@app.route('/<path:path>')
def send_js_path(path):
    return send_from_directory('.', path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send-sms', methods=['POST'])
@limiter.limit('2 per minute') # external config file can be used to configure the limit dynamically without being hardcoded
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
    subject = body.get('subject')
    message = f'Dear Mr/Mrs ' + client_name + ', '
    message += body.get('message')
    
    send_sms_to_client(client_contact, subject, message)
    store_message_in_db(subject, message, client_id)
    #return frontend expected JSON
    return jsonify({
        'success': True
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
    registration_ids = body.get('reg_ids')
    notification_title = body.get('title')
    notification_body = body.get('body')
    
    result = send_notification_to_devices(push_service, registration_ids, notification_title, notification_body)
    print(result)
    if isinstance(result, list):
        success = bool(result[0].get('success'))
    else:
        success = bool(result['success'])
    #if success:
    #    store_notification_in_db(notification_title, notification_body, client_id)
    return jsonify({
        'success': success
    }), 200

def send_notification_to_devices(push_service, registration_ids, notification_title, notification_body):
    if isinstance(registration_ids, list):
        # if passed registration ids list is empty, raise exception with status code: 400 Bad Request
        if registration_ids == []:
            raise RegistrationIDsNULLException(status_code=400)
        return push_service.notify_multiple_devices(registration_ids=registration_ids, message_body=notification_body, message_title=notification_title)
    else:
        return push_service.notify_single_device(registration_id=registration_ids, message_body=notification_body, message_title=notification_title)

def store_notification_in_db(title, body, client_id):
    current_time = datetime.now()
    new_notification = Notification(header=title, body=body, time=current_time, client_id=client_id)
    new_notification.insert()

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