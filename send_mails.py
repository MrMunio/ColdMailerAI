# send_mails.py
import smtplib
import csv
from email.message import EmailMessage
import os
from dotenv import load_dotenv
load_dotenv()

def send_emails_from_csv(csv_path: str, sender_email: str, sender_password: str, smtp_server='smtp.gmail.com', smtp_port=587):
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='|')
        for idx, row in enumerate(reader, start=1):
            recipient = row['Email']
            subject = row['Subject']
            body = row['Body']

            msg = EmailMessage()
            msg['From'] = sender_email
            # msg['To'] = recipient #------------>for production: sends to real emails.
            msg["To"]="jayaprakash91601@gmail.com" # ----------->for development purpose
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
    send_emails_from_csv(
        csv_path='composed_emails.csv',
        sender_email='sekharmuni003@gmail.com',
        sender_password=os.getenv("GOOGLE_APP_PASSWORD")  
    )
