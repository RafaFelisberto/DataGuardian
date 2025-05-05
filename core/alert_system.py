import smtplib
from slackweb import Slack

class AlertSystem:
    def __init__(self, slack_webhook=None, email_config=None):
        self.slack = Slack(url=slack_webhook) if slack_webhook else None
        self.email_config = email_config
    
    def send_slack_alert(self, message):
        if self.slack:
            self.slack.notify(text=message)
    
    def send_email_alert(self, subject, message):
        if not self.email_config:
            return
        
        server = smtplib.SMTP(self.email_config["smtp_server"], 
                             self.email_config["smtp_port"])
        server.starttls()
        server.login(self.email_config["username"], self.email_config["password"])
        server.sendmail(self.email_config["from"], self.email_config["to"], 
                       f"Subject: {subject}\n\n{message}")
        
def validate_recipient_email(email):
    if check_email_breach(email):
        raise ValueError(f"O e-mail {email} foi encontrado em vazamentos conhecidos.")