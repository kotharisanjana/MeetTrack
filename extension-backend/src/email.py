from common.aws_utilities import download_file_from_s3
import common.globals as global_vars
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

def send_email(object_key, local_file_path, recipient_email, meeting_name, meeting_date):
    download_file_from_s3(object_key, local_file_path)

    #email config
    recipient_email = recipient_email
    sender_email = global_vars.SENDER_EMAIL
    sender_password = global_vars.SENDER_PASSWORD
    subject = f"Meeting Notes from {meeting_name} on {meeting_date}"
    body = "Please find attached meeting notes from the meeting"

    # Create MIME multipart message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # Attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))

    # Open the file to be sent
    with open(local_file_path, "rb") as attachment:
        part = MIMEApplication(attachment.read(), Name=os.path.basename(local_file_path))

    # After the file is closed
    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(local_file_path)}"'
    msg.attach(part)

    # Setup the SMTP server
    try:
        server = smtplib.SMTP('smtp.example.com', 587)  # Use your SMTP server and port
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
