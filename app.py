from flask import Flask, request, jsonify, abort
import os
import pathlib
from werkzeug.exceptions import HTTPException
from datetime import datetime
import re

from models import Client, Message, Notification, setup_db
from exceptions import InvalidContactException, DatabaseInsertionException

#import firebase_admin
#from firebase_admin import credentials

#cred = credentials.Certificate(".\swvl-notifications-firebase-adminsdk-wf0zt-58b0f9ae56.json")
#default_app = firebase_admin.initialize_app(cred)

app = Flask(__name__)
setup_db(app)
contact_fixed_length = 13

@app.route('/')
def index():
    clients = Client.query.all()
    return clients[0].format()

@app.route('/send-sms', methods=['POST'])
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

if __name__ == "__main__":
    app.run('127.0.0.1', '5000', debug=True)