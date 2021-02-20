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