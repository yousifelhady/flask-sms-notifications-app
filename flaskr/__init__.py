from flask import Flask, request, jsonify, abort
import os
from sqlalchemy import Column, String, Integer, DateTime, create_engine
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pathlib
from werkzeug.exceptions import HTTPException
from datetime import datetime
import re

#import firebase_admin
#from firebase_admin import credentials

#cred = credentials.Certificate(".\swvl-notifications-firebase-adminsdk-wf0zt-58b0f9ae56.json")
#default_app = firebase_admin.initialize_app(cred)

#database section
database_filename = "swvl.db"
user = 'Yousif'
pw = 'yousif'
database_name = 'swvl'
#project_dir = os.path.dirname(os.path.abspath(__file__))
database_path = "postgresql://{}:{}@localhost:5432/{}".format(user, pw, database_name)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = database_path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
contact_fixed_length = 13

#database models
def db_drop_and_create_all():
    db.drop_all()
    db.create_all()

class Client(db.Model):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    contact = Column(String)
    name = Column(String)
    notifications = db.relationship('Notification', backref='client_notification', cascade='all,delete', lazy=True)
    messages = db.relationship('Message', backref='client_message', cascade='all,delete', lazy=True)
    
    def insert(self):
        try:
            db.session.add(self)
            db.session.commit()
        except:
            db.session.roll_back()

    def format(self):
        return {
            'id': self.id,
            'contact': self.contact,
            'notifications': [notification.format() for notification in Notification.query.filter_by(client_id=self.id).all()],
            'messages': [message.format() for message in Message.query.filter_by(client_id=self.id).all()]
        }
    
    def __repr__(self):
        return f'client id: {self.id}, contact: {self.contact}, name: {self.name}'
    
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    header = Column(String)
    body = Column(String)
    time = Column(DateTime, default=datetime.now())
    client_id = Column(Integer, db.ForeignKey('clients.id', ondelete='cascade'), nullable=False)

    def insert(self):
        try:
            db.session.add(self)
            db.session.commit()
        except:
            db.session.roll_back()
        
    def format(self):
        return {
            'id': self.id,
            'header': self.header,
            'body': self.body,
            'time': self.time,
            'client_id': self.client_id
        }

    def __repr__(self):
        return f'notf. id: {self.id}, header: {self.header}, body: {self.body}, time: {self.time}, client_id: {self.client_id}'

class Message(db.Model):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    subject = Column(String)
    body = Column(String)
    time = Column(DateTime, default=datetime.now())
    client_id = Column(Integer, db.ForeignKey('clients.id', ondelete='cascade'), nullable=False)

    def insert(self):
        try:
            db.session.add(self)
            db.session.commit()
            print(self)
        except Exception as ex:
            db.session.roll_back()
            raise DatabaseInsertionException(str(ex), 500)
    
    def format(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'body': self.body,
            'time': self.time,
            'client_id': self.client_id
        }

    def __repr__(self):
        return f'message id: {self.id}, subject: {self.subject}, body: {self.body}, time: {self.time}, client_id: {self.client_id}'

class InvalidContactException(Exception):
    def __init__(self, contact, status_code):
        self.contact = contact
        self.status_code = status_code

class DatabaseInsertionException(Exception):
    def __init__(self, exception_message, status_code):
        self.exception_message = exception_message
        self.status_code = status_code

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