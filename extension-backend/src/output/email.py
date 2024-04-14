from common.aws_utilities import download_file_from_s3
from database.relational_db import fetch_email, fetch_output_path
from __init__ import logger

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

def send_email(session_data):
    meeting_id = session_data["meeting_id"]
    meeting_name = session_data["meeting_name"]
    meeting_date = session_data["meeting_date"]
    local_output_path = session_data["local_output_path"]
    local_transcript_path = session_data["local_transcript_path"]
    
    # download final document from S3
    output_path = fetch_output_path(meeting_id)
    download_file_from_s3(output_path, local_output_path)

    # email config
    recipient_email = fetch_email(meeting_id)
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    subject = f"Notes & Transcript from {meeting_name} on {meeting_date}"
    body = "Hello, \n\n " + "Please find attached meeting notes and transcript. \n\n" + "Regards, \n" + "Team MeetTrack"

    # create MIME multipart message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))

    # open the meeting notes file to be sent
    with open(local_output_path, "rb") as attachment:
        part = MIMEApplication(attachment.read(), Name=os.path.basename(local_output_path))
    # after the file is closed
    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(local_output_path)}"'
    msg.attach(part)

    # open the transcript file to be sent
    with open(local_transcript_path, "rb") as attachment:
        part = MIMEApplication(attachment.read(), Name=os.path.basename(local_transcript_path))
    # after the file is closed
    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(local_transcript_path)}"'
    msg.attach(part)

    # setup the SMTP server and send email to the recipient
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
