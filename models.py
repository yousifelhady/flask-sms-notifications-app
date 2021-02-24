import os
from sqlalchemy import Column, String, Integer, DateTime, create_engine
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

from exceptions import DatabaseInsertionException

database_filename = "swvl.psql"
user = 'Yousif'
pw = 'yousif'
database_name = 'swvl'
#project_dir = os.path.dirname(os.path.abspath(__file__))
database_path = "postgresql://{}:{}@localhost:5432/{}".format(user, pw, database_name)

db = SQLAlchemy()

def setup_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)

#create a fresh version of database
def db_drop_and_create_all():
    db.drop_all()
    db.create_all()

class Client(db.Model):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    contact = Column(String)
    name = Column(String)
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
            'name': self.name,
            'messages': [message.format() for message in Message.query.filter_by(client_id=self.id).all()]
        }
    
    def __repr__(self):
        return f'client id: {self.id}, contact: {self.contact}, name: {self.name}'
    
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    body = Column(String)
    time = Column(DateTime, default=datetime.now())
    notificationtokens = db.relationship('TokenNotification', backref='notification_tokens', cascade='all,delete', lazy=True)

    def insert(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as ex:
            db.session.roll_back()
            raise DatabaseInsertionException(str(ex), 500)
        
    def format(self):
        return {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'time': self.time,
        }

    def __repr__(self):
        return f'notf. id: {self.id}, title: {self.title}, body: {self.body}, time: {self.time}'

class Token(db.Model):
    __tablename__ = 'tokens'
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True)
    tokennotifications = db.relationship('TokenNotification', backref='token_notifications', cascade='all,delete', lazy=True)

    def insert(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as ex:
            db.session.roll_back()
            raise DatabaseInsertionException(str(ex), 500)
        
    def format(self):
        return {
            'id': self.id,
            'token': self.token
        }

    def __repr__(self):
        return f'token: {self.token}'

# This class is used to map the Many to Many relationship between
# Tokens and Notifications as:
# Token can receive multiple notifications &
# Notification can be sent to multiple tokens
# This is not essential to have and can be replaced with nosql database for simplicity, 
# but I implemented it for data tracking purpose
class TokenNotification(db.Model):
    __tablename__ = 'tokennotifications'
    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, db.ForeignKey('tokens.id', ondelete='cascade'), nullable=False)
    notification_id = Column(Integer, db.ForeignKey('notifications.id', ondelete='cascade'), nullable=False)

    def insert(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as ex:
            db.session.roll_back()
            raise DatabaseInsertionException(str(ex), 500)
        
    def format(self):
        return {
            'id': self.id,
            'token_id': self.token_id,
            'notification_id': self.notification_id
        }

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