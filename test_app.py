import os
import unittest
import json
import time

from app import app, is_valid_contact_format
from models import Message, Notification
from config import api_limit_per_minute

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client

        self.invalid_contact = "01009129288"
        self.valid_contact = "+201009129288"
        self.sms_json = {
            'contact': self.valid_contact,
            'subject': 'testSubject',
            'message': 'test message body'
        }
        self.invalid_sms_json = {
            'subject': 'testSubject',
            'message': 'test message body'
        }
        self.topic_json = {
            'topic': "news",
            'title': 'test topic title',
            'body': 'test topic message body'
        }
        self.invalid_topic_json = {
            'title': 'test topic title',
            'body': 'test topic message body'
        }
        self.notification_json = {
            'tokens': [
                "dTWVMWRcwXARbMwcMBrz9V:APA91bHiaBYFTK_toYgFto3kNdlE9TaoJPPhEMSu1b0Yob20QH8D9j2RWQTalFgmJPv9oiCac-DBnexkd-rlsVhqGbcH0vqwZVPW2Q3tok1xQ56o9OJFUnBRaAjIHredgQkNZODi8xU2",
                "dyimeAKczeP3UJ8ynvI1I2:APA91bHQFAK2d28Tyfg89zqWVrPynCCEXF9eNnRW705fFxEdDE4klEBsqlVsdWiXl3jkWykCQ503Nh4m6EeL3tNS7iR1mnCB9e_Q7Sw_wDd_N3nENiqwmpTV2e1blahBck03zhR9t4LJ"
            ],
            'title': "test notification title",
            'body': "test notification message body"
        }
        self.invalid_notification_json = {
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
        res = self.client().post('/smss', json=self.sms_json)
        res_data = json.loads(res.data)
        sent_message = Message.query.order_by(Message.id.desc()).first()
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['success'], True)
        self.assertEqual(res_data['message_id'], sent_message.id)

    def test_send_sms_invalid_json_format(self):
        res = self.client().post('/smss', json=self.invalid_sms_json)
        res_data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res_data['success'], False)

    def test_send_sms_limit(self):
        #time.sleep(60)
        i = api_limit_per_minute + 1
        while i > 0:
            res = self.client().post('/smss', json=self.sms_json)
            i -= 1
        res_data = json.loads(res.data)

        self.assertEqual(res.status_code, 429)
        self.assertEqual(res_data['success'], False)

    def test_send_notification_to_topic(self):
        res = self.client().post('/notifications/topic', json=self.topic_json)
        res_data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['success'], True)

    def test_send_notification_to_topic_invalid_json_format(self):
        res = self.client().post('/notifications/topic', json=self.invalid_topic_json)
        res_data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res_data['success'], False)

    def test_send_notification_to_tokens(self):
        res = self.client().post('/notifications/tokens', json=self.notification_json)
        res_data = json.loads(res.data)
        sent_notification = Notification.query.order_by(Notification.id.desc()).first()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['success'], True)
        self.assertEqual(res_data['notification_id'], sent_notification.id)

    def test_send_notification_to_tokens_invalid_json_format(self):
        res = self.client().post('/notifications/tokens', json=self.invalid_notification_json)
        res_data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res_data['success'], False)

    def test_send_notification_to_tokens_no_json_body(self):
        res = self.client().post('/notifications/tokens')
        res_data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res_data['success'], False)

    # Testing HTTPException Handler
    # Example:
    def test_405_method_not_allowed(self):
        # PATCH request is not allowed for endpoint '/notifications/tokens'
        # 405: Method not allowed is returned
        res = self.client().patch('/notifications/tokens')
        res_data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(res_data['success'], False)
        self.assertEqual(res_data['message'], 'Method Not Allowed')

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