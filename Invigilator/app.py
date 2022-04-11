import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, abort, redirect, url_for
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant, ChatGrant
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)

mysql = MySQL()

app.config['SECRET_KEY'] = 'secret'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'demo'

mysql.init_app(app)

twilio_account_sid = "ACb72bc4e845ba95ef9ed6c4f74c795042"
twilio_api_key_sid = "SK834b234020512d079bfa8134a5c1344c"
twilio_api_key_secret = "vNapgud1k486nScq5J9QbIx5KQ1b8bcn"

load_dotenv()
twilio_account_sid = "ACb72bc4e845ba95ef9ed6c4f74c795042"
twilio_api_key_sid = "SK834b234020512d079bfa8134a5c1344c"
twilio_api_key_secret = "vNapgud1k486nScq5J9QbIx5KQ1b8bcn"

twilio_client = Client(twilio_api_key_sid, twilio_api_key_secret, twilio_account_sid)

global selected_courseID, selected_examID
selected_courseID = 0
selected_examID = 0

def get_chatroom(name):
    for conversation in twilio_client.conversations.conversations.stream():
        if conversation.friendly_name == name:
            return conversation

    return twilio_client.conversations.conversations.create(
        friendly_name=name)

def write_file(data, filename):        
    with open(filename, 'wb') as file:
        file.write(data)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('index.html')


@app.route('/retrieve', methods = ['GET', 'POST'])
def retrieve():
    if request.method == 'POST' and 'examID' in request.form:
        
        examID = request.form['examID']
        
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM scripts WHERE examID = %s', (examID, ))  
        # ALTERNATIVE: cur.execute('SELECT * FROM test_store_blob_image WHERE studentID = %s', (studentID, ))
        data = cur.fetchone()
        cur.close()
        
        for data in data:
            write_file(data[3], "static/downloadedscripts" + str(data[0])+".png")
        # ALTERNATIVE: write_file(data[1], "static/retrieved.png")  !! Note that image can be saved as either png or jpg

        return redirect(url_for('retrieve'), examID = examID)

    return render_template("retrieve.html")

@app.route('/readmatric', methods = ['GET', 'POST'])
def readmatric():
    if request.method == 'POST' and 'studentID' in request.form:
        
        studentID = request.form['studentID']

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM idimages WHERE studentID = %s', (studentID, ))
        data = cur.fetchall()
        cur.close()

        for data in data:
            write_file(data[1], "static/matriccard" + str(data[0])+".png")

        return redirect(url_for('readmatric'), studentID = studentID)

    return render_template("readmatric.html")

@app.route('/retrievedscript', methods = ['GET', 'POST'])
def retrievedscript():
    return render_template("retrievedscript.html")

@app.route('/afterreadmatric', methods = ['GET', 'POST'])
def afterreadmatric():
    return render_template("afterreadmatric.html")    

@app.route('/start', methods=['POST'])
def start():
    username = request.get_json(force=True).get('username')
    if not username:
        abort(401)

    conversation = get_chatroom('My Room')
    try:
        conversation.participants.create(identity=username)
    except TwilioRestException as exc:
        # do not error if the user is already in the conversation
        if exc.status != 409:
            raise

    token = AccessToken(twilio_account_sid, twilio_api_key_sid,
                        twilio_api_key_secret, identity=username)
    token.add_grant(VideoGrant(room='My Room'))
    token.add_grant(ChatGrant(service_sid=conversation.chat_service_sid))

    return {'token': token.to_jwt(), 'conversation_sid': conversation.sid}


if __name__ == '__main__':
        app.run(host='0.0.0.0', debug = True)
