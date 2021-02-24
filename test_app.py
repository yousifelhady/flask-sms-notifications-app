import os
import unittest
import json

from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client

        self.send_sms_json = {
            'contact': "+201009129288",
            'subject': 'testSubject',
            'message': 'testMessage'
        }

    def tearDown(self):
        pass
    
    def test_index(self):
        res = self.client().get('/')
        self.assertEqual(res.status_code, 200)

    def test_send_sms(self):
        res = self.client().post('/send-sms', json=self.send_sms_json)
        res_data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res_data['success'], True)
        self.assertEqual(res_data['contact'], self.send_sms_json['contact'])

    # def test_send_sms_limit(self):
    #     i = 4
    #     while i > 0:
    #         res = self.client().post('/send-sms', json=self.send_sms_json)
    #         i -= 1
    #     res_data = json.loads(res.data)

    #     self.assertEqual(res.status_code, 429)
    #     self.assertEqual(res_data['success'], False)

if __name__ == "__main__":
    unittest.main()