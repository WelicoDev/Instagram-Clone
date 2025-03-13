from celery import shared_task
from shared.utility import send_email , send_phone

@shared_task
def send_email_task(email, code):
    send_email(email, code)

@shared_task
def send_phone_task(phone, code):
    send_phone(phone, code)
from celery import shared_task
from shared.utility import send_email , send_phone

@shared_task
def send_email_task(email, code):
    send_email(email, code)

@shared_task
def send_phone_task(phone, code):
    send_phone(phone, code)
