import random
import sqlite3
from datetime import datetime

from flask import Flask, json, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.debug = True
connection = SocketIO(app)


# Method to read data from JSON file
def load_json(filename):
    with app.open_resource('static/' + filename + '.json') as j:
        return json.load(j)


def get_station_data():
    conn = sqlite3.connect('static/stations.db')
    cur = conn.cursor()

    station_names = [name[0] for name in cur.execute("SELECT name FROM stations")]
    station_codes = [code[0] for code in cur.execute("SELECT code FROM station_codes")]

    return station_names, station_codes


class Message(object):
    queue = ""

    # Add a message to the queue
    @staticmethod
    def queue_message(message):
        Message.queue += message

    # Show the ticket info on the UI
    @staticmethod
    def emit_ticket(event_name, ticket):
        connection.emit(event_name, ticket)

    # Show the chatbot's message on the UI with a message-timestamp sent
    @staticmethod
    def emit_message(event_name, message):
        message = {'message': Message.queue + message,
                   'time_sent': datetime.now().strftime("%H:%M")}
        Message.queue = ""
        connection.emit(event_name, message)

    # Add feedback to the queue
    @staticmethod
    def queue_feedback(feedback_name):
        feedback_list = load_json('chatbot_messages')[feedback_name]
        Message.queue += random.choice(feedback_list) + ' '

    # Show a message that may include additional info
    @staticmethod
    def emit_feedback(event_name, feedback_name, string=""):
        feedback_list = load_json('chatbot_messages')[feedback_name]
        feedback = Message.queue + random.choice(feedback_list)
        feedback = feedback.replace('%s', string)
        Message.queue = ""
        Message.emit_message(event_name, feedback)


# Get suffix type
def suffix(day):
    return 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')


# Get and return custom datetime containing suffix
def custom_strftime(date, type_format):
    return date.strftime(type_format).replace('{S}', str(date.day) + suffix(date.day))


# Get and return string as date
def get_strptime(string):
    return datetime.strptime(string, '%d%m%y')


# Get and return date in passed in format
def custom_to_date(string, type_format):
    return str(datetime.strftime(get_strptime(string), type_format))


# Render Index
@app.route('/')
def index():
    return render_template('index.html', stations=get_station_data())


# Import modules (having trouble putting them at the top of the file)
from nlpu import get_entities
from knowledge_base import get_nlpu_info


# Reset KB on first connect and display a greeting with first message
@connection.on('connect')
def connect():
    Message.queue_feedback('welcome')
    get_nlpu_info({'reset': 'true'})


# Handle the user's message
@connection.on('message sent')
def handle_message(json):
    # Display user message on the UI
    Message.emit_message('display sent message', json['message'])

    # Use NLPU and KB info to obtain feedback from chatbot
    get_nlpu_info(get_entities(json))


if __name__ == '__main__':
    connection.run(app)
