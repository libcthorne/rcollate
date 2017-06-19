import emails

import logs

from jinja2 import Environment, FileSystemLoader

TEMPLATES = Environment(loader=FileSystemLoader('templates'))
HTML_EMAIL_TEMPLATE = TEMPLATES.get_template("email_body.html.j2")

logger = logs.get_logger()

class Mailer(object):
    def __init__(self, smtp_host, smtp_timeout, sender_name, sender_email):
        self.smtp_host = smtp_host
        self.smtp_timeout = smtp_timeout
        self.sender_name = sender_name
        self.sender_email = sender_email

    def send_threads(self, r_threads, target_email, subreddit):
        logger.info("Send /r/{} threads to {}".format(subreddit, target_email))

        message = emails.html(
            html=HTML_EMAIL_TEMPLATE.render(r_threads=r_threads),
            subject="Top threads in /r/{}".format(subreddit),
            mail_from=(self.sender_name, self.sender_email)
        )

        r = message.send(
            to=target_email,
            smtp={'host': self.smtp_host, 'timeout': self.smtp_timeout}
        )

        success = (r.status_code == 250)

        if success:
            logger.info("Sent /r/{} email to {}".format(
                subreddit, target_email
            ))
        else:
            logger.error("Error sending /r/{} email to {}: status_code={}, err={}".format(
                subreddit, target_email, r.status_code, r.error
            ))

        return success
