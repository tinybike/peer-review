#!/usr/bin/env python
"""
peer review app

"""
from __future__ import division
from gevent import monkey
monkey.patch_all()
try:
    from psycopg2cffi import compat
    compat.register()
except:
    pass
import sys
try:
    import cdecimal
    sys.modules["decimal"] = cdecimal
except:
    pass
import random
import base64
import string
import hashlib
from Crypto.Cipher import AES
from decimal import *
import bcrypt
from flask import Flask, session, request, escape, flash, url_for, redirect, render_template, g, send_from_directory
from flask.ext.login import login_user, logout_user, current_user, login_required, LoginManager
from flask.ext.socketio import SocketIO, emit
from flask.sessions import SessionInterface, SessionMixin
from itsdangerous import URLSafeTimedSerializer, BadSignature
from werkzeug.datastructures import CallbackDict
from werkzeug import secure_filename
from contextlib import contextmanager
try:
    import psycopg2cffi as db
    import psycopg2cffi.extensions as ext
    from psycopg2cffi.extras import RealDictCursor
except:
    import psycopg2 as db
    import psycopg2.extensions as ext
    from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.config.from_object('config')
app.debug = True

socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

class User(object):

    def __init__(self, id=None, username=None, email=None):
        self.id = id
        self.username = username
        self.email = email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

class ItsdangerousSession(CallbackDict, SessionMixin):

    def __init__(self, initial=None):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.modified = False


class ItsdangerousSessionInterface(SessionInterface):
    salt = 'cookie-session'
    session_class = ItsdangerousSession

    def get_serializer(self, app):
        if not app.secret_key:
            return None
        return URLSafeTimedSerializer(app.secret_key, 
                                      salt=self.salt)

    def open_session(self, app, request):
        s = self.get_serializer(app)
        if s is None:
            return None
        val = request.cookies.get(app.session_cookie_name)
        if not val:
            return self.session_class()
        max_age = app.permanent_session_lifetime.total_seconds()
        try:
            data = s.loads(val, max_age=max_age)
            return self.session_class(data)
        except BadSignature:
            return self.session_class()

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            if session.modified:
                response.delete_cookie(app.session_cookie_name,
                                   domain=domain)
            return
        expires = self.get_expiration_time(app, session)
        val = self.get_serializer(app).dumps(dict(session))
        response.set_cookie(app.session_cookie_name, val,
                            expires=expires, httponly=True,
                            domain=domain)

def connect():
    '''Returns a postgres database connection'''
    conn = db.connect(
            host=app.config.get('POSTGRES_HOST'),
            user=app.config.get('POSTGRES_USER'),
            password=app.config.get('POSTGRES_PASSWORD'),
            database=app.config.get('POSTGRES_DATABASE'),
            port=app.config.get('POSTGRES_PORT')
    )
    return conn

@contextmanager
def cursor(cursor_factory=False):
    '''
    Database cursor generator: handles connection, commit, rollback,
    error trapping, and closing connection.  Will propagate exceptions.
    '''
    conn = None
    try:
        conn = connect()
        if not conn or conn.closed:
            attempt = 1
            while attempt < 5 and (not conn or conn.closed):
                print "Attempt:", attempt
                time.sleep(5)
                attempt += 1
                conn = db.connect(host=params[0],
                                  user=params[1],
                                  password=params[2],
                                  database=params[3],
                                  port=params[4])
        if not conn or conn.closed:
            raise Exception("Database connection failed after %d attempts." % attempt)
        if cursor_factory:
            cur = conn.cursor(cursor_factory=db.extras.RealDictCursor)
        else:
            cur = conn.cursor()
        yield cur
    except (db.Error, Exception) as err:
        if conn:
            conn.rollback()
            conn.close()
        print err.message
        raise
    else:
        conn.commit()
        conn.close()


class Guard(object):

    MISMATCH_ERROR = TypeError("inputs must be both unicode or both bytes")

    def AES_cipher(self, cleartext, password):
        key = hashlib.sha256(password).digest()
        iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
        encryptor = AES.new(key, AES.MODE_CBC, IV=iv)
        ciphertext = encryptor.encrypt(cleartext + 'XXX')
        return ciphertext, iv

    def AES_clear(self, ciphertext, password, iv):
        key = hashlib.sha256(password).digest()
        decryptor = AES.new(key, AES.MODE_CBC, IV=iv)
        return decryptor.decrypt(ciphertext)[:-3]

    def bcrypt_digest(self, password):
        return bcrypt.hashpw(password, bcrypt.gensalt())

    def check_password(self, password, digest):
        return self.const_time_compare(bcrypt.hashpw(password, digest), digest)

    def const_time_compare(self, a, b):
        result = False
        if isinstance(a, unicode):
            if not isinstance(b, unicode):
                raise MISMATCH_ERROR
        elif isinstance(a, bytes):
            if not isinstance(b, bytes):
                raise MISMATCH_ERROR
        else:
            raise MISMATCH_ERROR
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        return result == 0

    def id_generator(self, size=6, chars=string.ascii_uppercase+string.ascii_lowercase+string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1] in config.ALLOWED_EXTENSIONS


guard = Guard()

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

############
# Register #
############

@app.before_request
def before_request():
    g.user = current_user
    g.debug = True if app.debug else False

def check_username_taken(requested_username):
    with cursor() as cur:
        cur.execute("SELECT count(*) FROM users WHERE username = %s",
                    (requested_username,))
        if cur.rowcount:
            username_taken = cur.fetchone()[0]
    if username_taken > 0:
        return True
    return False

def insert_user(username, password, email):
    dyff_freebie = '100'
    insert_user_parameters = {
        'username': username,
        'password': guard.bcrypt_digest(password.encode('utf-8')),
        'email': email,
    }
    insert_user_query = (
        "INSERT INTO users "
        "(username, password, email, joined) "
        "VALUES "
        "(%(username)s, %(password)s, %(email)s, now()) "
        "RETURNING user_id"
    )
    insert_result = None
    with cursor() as cur:
        cur.execute(insert_user_query, insert_user_parameters)
        if cur.rowcount:
            insert_result = cur.fetchone()[0]
    return insert_result

def create_session(userid, username, password, email):
    user = User(userid, username, email)
    login_user(user)
    session['user'] = escape(user.username)
    return user, session

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if not check_username_taken(request.form['username']):
        insert_result = insert_user(
            request.form['username'],
            request.form['password'],
            request.form['email']
        )
        # Success
        if insert_result is not None:
            user, session = create_session(insert_result,
                                           request.form['username'],
                                           request.form['password'],
                                           request.form['email'])
            return render_template('index.html', registration_ok=True)
        # Failure
        else:
            user = None
            return render_template('index.html', registration_ok=False)
    else:
        print "Username", request.form['username'], "taken"
        return render_template('register.html', err="Username taken")

#########
# Login #
#########

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('index'))
        else:
            return render_template('login.html')
    user = None
    with cursor(True) as cur:
        query = (
            "SELECT user_id, password, email, admin FROM users "
            "WHERE username = %s"
        )
        cur.execute(query, (request.form['username'],))
        for row in cur:
            stored_password_digest = row['password']
            if guard.check_password(request.form['password'].encode('utf-8'), 
                                    stored_password_digest):
                user = User(row['user_id'],
                            request.form['username'],
                            row['email'])
                admin = row['admin']
    if user is None or user.id is None:
        flash('Username or password is invalid', 'error')
        return redirect(url_for('login'))
    with cursor() as cur:
        query = "UPDATE users SET active = now() WHERE user_id = %s"
        cur.execute(query, (user.id,))
    login_user(user)
    session['user'] = escape(user.username)
    session['admin'] = admin
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user', None)
    session.pop('user_id', None)
    session.pop('address', None)
    session.pop('secret', None)
    session.pop('admin', None)
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user_id):
    user = None
    query = "SELECT user_id, username, email FROM users WHERE user_id = %s"
    with cursor(True) as cur:
        cur.execute(query, (str(user_id),))
        if cur.rowcount:
            res = cur.fetchone()
            user = User(res['user_id'], res['username'], res['email'])
    return user

##########
# Upload #
##########

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and guard.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

#############
# Reviewing #
#############

@socketio.on('get-users', namespace='/socket.io/')
def get_users():
    users, report_ids = [], []
    if 'user_id' in session:
        with cursor() as cur:
            query = "SELECT username FROM users WHERE user_id <> %s"
            cur.execute(query, (session['user_id'],))
            for row in cur:
                users.append(row[0])
        emit('users', {'users': users, 'report_id': report_ids})

@socketio.on('get-all-reports', namespace='/socket.io/')
def get_all_reports():
    reports = []
    if 'user_id' in session:
        with cursor(True) as cur:
            query = "SELECT report_id, username, report, reporttime FROM reports WHERE user_id <> %s ORDER BY reporttime DESC"
            cur.execute(query, (session['user_id'],))
            for row in cur:
                reports.append({
                    'report_id': row['report_id'],
                    'username': row['username'],
                    'timestamp': row['reporttime'],
                })
        emit('all-reports', {'reports': reports})

@socketio.on('get-reports', namespace='/socket.io/')
def get_reports(req):
    reports, timestamps = [], []
    if 'user_id' in session:
        with cursor() as cur:
            userquery = "SELECT user_id FROM users WHERE user_id = %s"
            cur.execute(userquery, (req['username'],))
            for row in cur:
                user_id = row[0]
            query = "SELECT report, reporttime from reports WHERE user_id = %s"
            cur.execute(query, (user_id,))
            for row in cur:
                reports.append(row[0])
                timestamps.append(row[1])
        emit('reports', {'reports': reports, 'timestamps': timestamps})

@socketio.on('submit-review', namespace='/socket.io/')
def submit_review(req):
    review_id = None
    if 'user_id' in session:
        with cursor() as cur:
            upsertquery = "SELECT count(*) FROM reviews WHERE report_id = %s"
            cur.execute(upsertquery, (req['report_id'],))
            for row in cur:
                count = row[0]
                if count > 0:
                    query = (
                        "UPDATE reviews "
                        "SET rating = %(rating)s AND comments = %(comments)s AND "
                        "reviewer = %(reviewer)s AND reviewee = %(reviewee)s "
                        "WHERE report_id = %(report_id)s "
                        "RETURNING review_id"
                    )
                    params = {
                        'rating': req['rating'],
                        'comments': req['comments'],
                        'reviewer': session['user'],
                        'reviewee': req['reviewee'],
                        'report_id': req['report_id'],
                    }
                else:
                    query = (
                        "INSERT INTO reviews "
                        "(report_id, reviewer, reviewee, rating, comments) "
                        "VALUES "
                        "(%(report_id)s, %(reviewer)s, %(reviewee)s, %(rating)s, %(comments)s) "
                        "RETURNING review_id"
                    )
                    params = {
                        'report_id': req['report_id'],
                        'reviewer': session['user'],
                        'reviewee': req['reviewee'],
                        'rating': req['rating'],
                        'comments': req['comments'],
                    }
            cur.execute(query, params)
            for row in cur:
                review_id = row[0]
        emit('review-submitted', {'review_id': review_id})

@socketio.on('get-report', namespace='/socket.io/')
def get_report(req):
    report, timestamp, mean_rating = None, None, None
    if 'user_id' in session:
        with cursor() as cur:
            query = "SELECT report, reporttime FROM reports WHERE report_id = %s"
            cur.execute(query, (req['report-id'],))
            for row in cur:
                report = row[0]
                timestamp = row[1]
            reviewquery = (
                "SELECT rating FROM reviews WHERE report_id = %s "
                "ORDER BY reviewtime LIMIT 1"
            )
            cur.execute(reviewquery, (req['report-id'],))
            for row in cur:

        emit('report', {
            'report': report,
            'timestamp': timestamp,
            'report_id': req['report-id'],
            'username': req['username'],

        })

@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'GET':
        return render_template('report.html')
    report_id = None
    with cursor() as cur:
        params = {
            'user_id': session['user_id'],
            'username': session['user'],
            'report': request.form['report-text'],
        }
        query = (
            "INSERT INTO reports (user_id, username, report) VALUES "
            "(%(user_id)s, %(username)s, %(report)s) "
            "RETURNING report_id"
        )
        cur.execute(query, params)
        if report_id is not None:
            return redirect(url_for('submitted'))
    return render_template('report.html')

@app.route('/submitted')
def submitted():
    render_template('submitted.html')

def main():
    if app.config['DEBUG']:
        socketio.run(app)
    else:
        socketio.run(app, host='0.0.0.0', port=8080)

if __name__ == "__main__":
    main()
