from flask import Flask
import os

class InvalidContactException(Exception):
    def __init__(self, contact, status_code):
        self.contact = contact
        self.status_code = status_code

class DatabaseInsertionException(Exception):
    def __init__(self, exception_message, status_code):
        self.exception_message = exception_message
        self.status_code = status_code

class RegistrationIDsNULLException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code

class JSONBodyFormatException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code

class MissingJSONBodyException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code