import re
import threading
from twilio.rest import Client

from decouple import config
import phonenumbers
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
phone_regax = r'^\+998(9[1-5]|33|50|77|71)\d{7}$'
username_regax = r'^[a-zA-Z0-9_]{4,32}$'

def check_email_or_phone(email_or_phone):
    if re.fullmatch(email_regex, email_or_phone):
        email_or_phone = "email"
    elif phonenumbers.is_valid_number(phonenumbers.parse(email_or_phone)):
        email_or_phone = "phone"
    else:
        data = {
            "success":False,
            "message":"Email or phone number invalid."
        }
        raise ValidationError(data)

    return email_or_phone

def check_user_type(user_input):
    if re.fullmatch(email_regex, user_input):
        user_input = "email"
    elif re.fullmatch(phone_regax, user_input):
        user_input = "phone"
    elif re.fullmatch(username_regax, user_input):
        user_input = "username"
    else:
        error = {
            "Success":False,
            "message":"Username or email or phone number is invalid."
        }

        raise ValidationError(error)

    return user_input



class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email

        threading.Thread.__init__(self)

    def run(self):
        self.email.send()

class Email:
    @staticmethod
    def send_email(data):
        # Creating email object
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            to=[data['to_email']]
        )

        # Check if the content type is HTML
        if data.get('content_type') == "html":
            email.content_subtype = "html"

        # Starting a new thread for sending the email asynchronously
        EmailThread(email).start()

def send_email(email, code):
    # Render the HTML content using the template
    html_content = render_to_string(
        'email/authentication/activate_account.html',
        {"code": code},
    )

    # Send the email with the generated HTML content
    Email.send_email(
        {
            "subject": "Activate Your Account",
            "to_email": email,
            "body": html_content,
            "content_type": "html"
        }
    )

def send_phone(phone, code):
    account_sid = config('account_sid')
    auth_token = config("auth_token")
    client = Client(account_sid, auth_token)

    client.messages.create(
        body = f"Hello my friend !\n Your confirmed code : {code}",
        from_ = f"{config("phone_number")}",
        to =f"{phone}"
    )

