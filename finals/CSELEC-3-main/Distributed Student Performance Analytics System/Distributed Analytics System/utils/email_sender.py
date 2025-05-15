import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def send_grade_notification(email, subject_code, grade):
    try:
        # Email configuration
        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))

        # Create message
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = email
        message['Subject'] = f'Grade Update Notification - {subject_code}'

        # Email body
        body = f"""
        Hello,

        Your grade for {subject_code} has been submitted!
        Your Grade is {grade}

        Best regards,
        Student Performance Analytics System
        """

        message.attach(MIMEText(body, 'plain'))

        # Create SMTP session
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)

        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e) 