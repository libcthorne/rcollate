import re

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Regexp, ValidationError

import rcollate.reddit as reddit

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

class JobForm(FlaskForm):
    subreddit = StringField(
        'Subreddit',
        validators=[
            DataRequired(
                message="Please enter a subreddit",
            ),
        ]
    )

    target_email = StringField(
        'Target email',
        validators=[
            DataRequired(
                message="Please enter an email address",
            ),
            Regexp(
                EMAIL_REGEX,
                message="Please enter a valid email address",
            ),
        ]
    )

    def validate_subreddit(form, field):
        if not reddit.subreddit_exists(field.data):
            raise ValidationError("Subreddit not found")
