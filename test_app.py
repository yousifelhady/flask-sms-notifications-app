import os
import unittest
import json
import time

from app import app, is_valid_contact_format
from models import Message, Notification

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client

        self.invalid_contact = "01009129288"
        self.valid_contact = "+201009129288"
        self.send_valid_sms_json = {
            'contact': self.valid_contact,
            'subject': 'testSubject',
            'message': 'test message body'
        }
        self.send_topic_json = {
            'topic': "news",
            'title': 'test topic title',
            'body': 'test topic message body'
        }
        self.send_notification_json = {
            'tokens': [
                "dTWVMWRcwXARbMwcMBrz9V:APA91bHiaBYFTK_toYgFto3kNdlE9TaoJPPhEMSu1b0Yob20QH8D9j2RWQTalFgmJPv9oiCac-DBnexkd-rlsVhqGbcH0vqwZVPW2Q3tok1xQ56o9OJFUnBRaAjIHredgQkNZODi8xU2",
                "dyimeAKczeP3UJ8ynvI1I2:APA91bHQFAK2d28Tyfg89zqWVrPynCCEXF9eNnRW705fFxEdDE4klEBsqlVsdWiXl3jkWykCQ503Nh4m6EeL3tNS7iR1mnCB9e_Q7Sw_wDd_N3nENiqwmpTV2e1blahBck03zhR9t4LJ"
            ],
            'title': "test notification title",
            'body': "test notification message body"
        }
        
    def tearDown(self):
        pass
    
    # Testing Endpoints
    ###################
    def test_index(self):
        res = self.client().get('/')
        self.assertEqual(res.status_code, 200)

    def test_send_sms(self):
        res = self.client().post('/send-sms', json=self.send_valid_sms_json)
        res_data = json.loads(res.data)
        sent_message = Message.query.order_by(Message.id.desc()).first()
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['success'], True)
        self.assertEqual(res_data['contact'], self.send_valid_sms_json['contact'])
        self.assertTrue(res_data['message'])
        self.assertEqual(res_data['message_id'], sent_message.id)

    def test_send_sms_limit(self):
        #time.sleep(60)
        i = 4
        while i > 0:
            res = self.client().post('/send-sms', json=self.send_valid_sms_json)
            i -= 1
        res_data = json.loads(res.data)

        self.assertEqual(res.status_code, 429)
        self.assertEqual(res_data['success'], False)

    def test_notify_topic(self):
        res = self.client().post('/notify-topic', json=self.send_topic_json)
        res_data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['success'], True)
        self.assertEqual(res_data['topic'], self.send_topic_json['topic'])
        self.assertTrue(res_data['title'])
        self.assertTrue(res_data['body'])

    def test_send_notification(self):
        res = self.client().post('/send-notification', json=self.send_notification_json)
        res_data = json.loads(res.data)
        sent_notification = Notification.query.order_by(Notification.id.desc()).first()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['success'], True)
        self.assertEqual(res_data['tokens'], self.send_notification_json['tokens'])
        self.assertTrue(res_data['title'])
        self.assertTrue(res_data['body'])
        self.assertEqual(res_data['notification_id'], sent_notification.id)

    # Testing Helper functions
    ##########################
    def test_is_valid_contact_format_with_invalid_contact(self):
        tested_value = is_valid_contact_format(self.invalid_contact)
        expected_value = False
        self.assertEqual(expected_value, tested_value)

    def test_is_valid_contact_format_with_valid_contact(self):
        tested_value = is_valid_contact_format(self.valid_contact)
        expected_value = True
        self.assertEqual(expected_value, tested_value)

if __name__ == "__main__":
    unittest.main()