import os
from sqlalchemy import Column, String, Integer, DateTime, create_engine
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

database_filename = "swvl.db"
user = 'Yousif'
pw = 'yousif'
database_name = 'swvl'
#project_dir = os.path.dirname(os.path.abspath(__file__))
database_path = "postgresql://{}:{}@localhost:5432/{}".format(user, pw, database_name)

def setup_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)

def db_drop_and_create_all():
    db.drop_all()
    db.create_all()

class Client(db.Model):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    contact = Column(String)
    notifications = db.relationship('Notification', backref='client_notification', cascade='all,delete', lazy=True)
    messages = db.relationship('Message', backref='client_message', cascade='all,delete', lazy=True)
    
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    header = Column(Integer)
    body = Column(Integer)
    time = Column(DateTime)
    client_id = Column(Integer, db.ForeignKey('clients.id', ondelete='cascade'), nullable=False)

class Message(db.Model):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    header = Column(Integer)
    body = Column(Integer)
    time = Column(DateTime)
    client_id = Column(Integer, db.ForeignKey('clients.id', ondelete='cascade'), nullable=False)