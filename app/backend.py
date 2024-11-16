import firebase_admin
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO
from datetime import datetime
from db_manager import DatabaseManager
from mqtt_manager import MQTTManager
from flask import Flask, render_template, redirect, url_for, request, session
from firebase_admin import credentials, auth
from functools import wraps

"""
    Socket and Flask
"""
app = Flask(__name__)
app.secret_key = 'ss2'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

"""
   DB and MQTT Handler 
"""
db_manager = DatabaseManager()
mqtt_manager = MQTTManager(db_manager)

"""
   Creds
"""
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)

"""
   Login req
"""
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'uid' not in session:
            return render_template('access_denied.html')
        return f(*args, **kwargs)
    return decorated_function

"""
   login page
"""
@app.route('/')
def index():
    return render_template('login.html')

"""
   login method
"""
@app.route('/login', methods=['POST'])
def login():
    id_token = request.form.get('idToken')
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        session['uid'] = uid
        return redirect(url_for('index'))
    except Exception as e:
        print("Error verifying ID token:", e)
        return redirect(url_for('login'))

"""
   Main app
"""
@app.route('/index')
@login_required
def dashboard():
    # return f"Welcome to your dashboard, User ID: {session['uid']}"
    return render_template('index.html')

"""
   Logout method
"""
@app.route('/logout')
def logout():
    session.pop('uid', None)
    return redirect(url_for('index'))

"""
   Historical data req
   Format : /api/fetch_data?startdate=YYYY-MM-DD%20hh:mm:ss&enddate=YYYY-MM-DD%20hh:mm:ss
"""
@app.route('/api/fetch_data', methods=['GET'])
def get_fetch_data():
    startdate_str = request.args.get('startdate')
    enddate_str = request.args.get('enddate')

    startdate = datetime.strptime(startdate_str, "%Y-%m-%d %H:%M:%S") if startdate_str else None
    enddate = datetime.strptime(enddate_str, "%Y-%m-%d %H:%M:%S") if enddate_str else None
    
    raw_data = db_manager.get_data(startdate, enddate)
    
    data = [
        {
            "id": item[0],
            "reading_time": item[1].strftime("%Y-%m-%d %H:%M:%S"),
            "position": item[2],
            "meter_type": item[3],
            "meter_serial_number": item[4],
            "active_energy_import": item[5],
            "active_energy_export": item[6],
            "reactive_energy_import": item[7],
            "reactive_energy_export": item[8],
            "apparent_energy_import": item[9],
            "apparent_energy_export": item[10]
        }
        for item in raw_data
    ]
    
    return jsonify(data)

"""
    Main
"""
if __name__ == '__main__':
    mqtt_manager.start_mqtt_loop()
    socketio.run(app, host='0.0.0.0', port='5000', debug=False)