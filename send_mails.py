# send_mails.py
import smtplib
import csv
from email.message import EmailMessage
import os
from dotenv import load_dotenv
load_dotenv()

FAKE_RECEIVER_EMAIL_ID=os.getenv("FAKE_RECEIVER_EMAIL_ID","fake_account@email.com")
REDIRECT_EMAILS_TO_FAKE_RECEIVER=os.getenv("REDIRECT_EMAILS_TO_FAKE_RECEIVER","true")
REDIRECT_EMAILS_TO_FAKE_RECEIVER = REDIRECT_EMAILS_TO_FAKE_RECEIVER.lower()=="true"

def send_emails_from_csv(csv_path: str, sender_email: str, sender_password: str, smtp_server='smtp.gmail.com', smtp_port=587):
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='|')
        for idx, row in enumerate(reader, start=1):
            recipient = row['Email']
            subject = row['Subject']
            body = row['Body']

            msg = EmailMessage()
            msg['From'] = sender_email

            # check if emails are to send to actula receiver emial accouts
            if REDIRECT_EMAILS_TO_FAKE_RECEIVER:
                msg["To"]=FAKE_RECEIVER_EMAIL_ID # ----------->for development purpose
            else:
                msg['To'] = recipient #------------>for production: sends to real emails.

            msg['Subject'] = subject
            msg.set_content(body)

            try:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                print(f"✅ Sent email {idx} to {recipient}")
            except Exception as e:
                print(f"❌ Failed to send email to {recipient}: {e}")

if __name__=="__main__":
    # Example usage
    SENDER_EMAIL=os.getenv("SENDER_EMAIL","")
    GOOGLE_APP_PASSWORD = os.getenv("GOOGLE_APP_PASSWORD")
    send_emails_from_csv(
        csv_path=r'output\composed_emails_20250422_145819.csv',
        sender_email=SENDER_EMAIL,
        sender_password= GOOGLE_APP_PASSWORD
    )
