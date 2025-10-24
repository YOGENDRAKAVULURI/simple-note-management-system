import smtplib # for sending emails
from email.message import EmailMessage 
def send_email(to, subject, body):
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465) # create server object for gmail
    server.login("kavuluriyogendra@gmail.com","ohfa wmmb tpmu zlkw") # login to your email account
    msg = EmailMessage()
    msg['From'] = "kavuluriyogendra@gmail.com"
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)
    server.send_message(msg)
    server.close()