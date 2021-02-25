#!/bin/bash
cd flask-sms-notifications-app
pip3 install -r requirements.txt
export FLASK_APP=app.py
flask db upgrade
python3 app.py
