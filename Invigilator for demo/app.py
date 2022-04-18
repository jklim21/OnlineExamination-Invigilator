import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, abort, redirect, url_for, session, flash
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

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'domain' in request.form:
        
        username = request.form['username']
        password = request.form['password']
        domain = request.form['domain']

        if domain == '1':   # Student 
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM students WHERE username = % s AND password = % s', (username, password, ))
            account = cursor.fetchone()

            if account:
                session['id'] = account['studentID']
                session['name'] = account['name']

                return redirect(url_for('!#'))
                
            else:

                flash('Student does not exist with the entered username and password!')
        
        if domain == '2': # Admin
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM invigilators WHERE username = % s AND password = % s AND admin = "yes"', (username, password, ))
            account = cursor.fetchone()

            if account:
                session['id'] = account['invigilatorID']
                session['name'] = account['name']

                #return render_template('index.html')     # CHANGE TO ADMIN's FIRST PAGE
                return redirect(url_for('!#'))

            else:

                flash('Admin does not exist with the entered username and password!')

        if domain == '3': # Invigilator
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM invigilators WHERE username = % s AND password = % s AND admin = "no"', (username, password, ))
            account = cursor.fetchone()

            if account:
                session['id'] = account['invigilatorID']
                session['name'] = account['name']

                return redirect(url_for('readmatric'))     # CHANGE TO INVIGILATORS'S FIRST PAGE

            else:
                
                flash('Invigilator does not exist with the entered username and password!')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('readmatric.html')

@app.route('/waitingroom')
def waitingroom():
    return render_template('waitingroom.html')


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

@app.route('/video')
def video():
    return render_template('video.html')    

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
