from pa.plugin import Plugin
import pa
from flask import Flask


class FlaskServer(Plugin):
    __pluginname__ = 'flask_server'

    def on_load(self):
        pa.web_app = Flask(__name__)

    def run_server(self):
        pa.web_app.run(host=pa.server_ip, port=int(pa.server_port), threaded=True)
