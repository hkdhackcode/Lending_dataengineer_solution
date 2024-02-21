from database_service import Database, calculate_frequency
from string import Template
import database_service
import schedule
import time
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import psycopg2
from psycopg2 import sql
from datetime import datetime
import pandas as pd
import os

class MailTemplate:
    def __init__(self, filename, values = {}):
        self.filename = filename
        self.values = values

    def generate(self):
        with open(self.filename, 'r', encoding='utf-8') as template_file:
            template_file_content = template_file.read()
            mail_template = Template(template_file_content)
            body = mail_template.substitute(self.values)
        return body

def send_mail(config, user_email, subject='', body='', file_attachments = []):
    # Create the email message
    message = MIMEMultipart()
    message['From'] = config["SENDER_EMAIL"]
    message['To'] = user_email
    message['Subject'] = subject
    
    message.attach(MIMEText(body, 'plain'))

    for attachment in file_attachments:
        with open(attachment, "rb") as f:
            filename = os.path.basename(attachment)
            part = MIMEApplication(f.read(), Name=filename)
            part['Content-Disposition'] = 'attachment; filename="' + str(filename) + '"'
            message.attach(part)

    # Connect to SMTP server and send the email
    try:
        with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"]) as server:
            server.starttls()
            print("Login into server: ")
            server.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
            print("Sending mail:")
            server.sendmail(config["SENDER_EMAIL"], user_email, message.as_string())
            return "Success"
    except:
        print("NOt able to send it.")
        return "Fail"


def send_payment_reminder():
    config = json.load(open('config.json'))
    try:
        results = Database(config["db"]).check_due_payment()
        for result in results:
            user_id, user_name, user_email, due_amount, due_date, due_in = result
            values = {
                "user_id": user_id,
                "user_name": user_name,
                "user_email": user_email,
                "due_amount": due_amount,
                "due_date": due_date.date()
                
            }
            body = MailTemplate("reminder.text", values).generate()
            frequency = calculate_frequency(due_in)
            send_mail(config['mail'], values["user_email"], "Loan Payment Reminder", body)
            print("Mail send successful")
            
    except psycopg2.Error as e:
        print(f"Error querying due payments: {e}")


def write_in_excel(output, filename):
    print("Staring to write")
    columns = output[1]
    data = output[0]
    df = pd.DataFrame(list(data), columns=columns)

    writer = pd.ExcelWriter(filename)
    df.to_excel(writer, sheet_name='summary')
    writer.save()
    print("Data written in excel successfully.")


def send_summary_report():
    config = json.load(open('config.json'))
    try:
        db = Database(config["db"])
        week_results = db.get_last_week_status()
        overall_summary = db.get_overall_summary()
        overall_summary_monthly = db.get_overall_summary_monthly()
        
        loan_issued, total_loan_amount, loan_paid, total_paid_amount = week_results[0]
        values = {
            "loan_issued": loan_issued, 
            "total_amount_issued": total_loan_amount, 
            "loan_paid": loan_paid, 
            "amount_paid": total_paid_amount,
            "date": datetime.now().date(),
            "Recipient":"Harsh",
            "user_email": config["mail"]["team_mail"]
                
        }
        body = MailTemplate("summary.text", values).generate()

        write_in_excel(overall_summary, "overall_summary.xlsx")
        write_in_excel(overall_summary_monthly, "overall_summary_monthly.xlsx")



            
        send_mail(config['mail'], values["user_email"], "Weekly Loan Operations Summary", body, file_attachments=["overall_summary.xlsx", "overall_summary_monthly.xlsx"])
        print(f"Weekly report is sent.")
    except psycopg2.Error as e:
        print(f"Error querying due payments: {e}")


        


#send_summary_report()
if __name__ == "__main__":
    schedule.every(2).days.do(send_summary_report)
    schedule.every(2).days.do(send_payment_reminder)
    while True:
        schedule.run_pending()
        time.sleep(1)
    #config = json.load(open('config.json'))
    #send_mail(config["mail"], "harshkumardubey11@gmail.com", "tesing", "Able to send mail")