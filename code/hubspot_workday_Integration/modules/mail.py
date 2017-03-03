import smtplib

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

from configuration import mail_cfg

user = mail_cfg.defaults()["user"]
password = mail_cfg.defaults()["password"]

def send(to, subject, content):

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = to
    msg['Subject'] = subject
    message = content
    msg.attach(MIMEText(message))

    mailserver = smtplib.SMTP('smtp.gmail.com', 25)
    #mailserver.set_debuglevel(True)
    # identify ourselves to smtp gmail client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login(user, password)

    mailserver.sendmail(user, to, msg.as_string())

    mailserver.quit()
