from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_notification_email(user, message):
    subject = "Notification"
    context = {"user": user, "message": message}

    text_body = render_to_string("emails/notification.txt", context)
    html_body = render_to_string("emails/notification.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()