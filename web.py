import mailer

from flask import Flask
from jinja2 import Environment, FileSystemLoader

TEMPLATES = Environment(loader=FileSystemLoader('.'))
INDEX_TEMPLATE = TEMPLATES.get_template("index.html.j2")

app = Flask(__name__)

@app.route("/")
def index():
    return INDEX_TEMPLATE.render(jobs=mailer.jobs)

mailer.start()
