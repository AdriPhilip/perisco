from flask import Flask, request, session, redirect, url_for, jsonify
from flaskext.mysql import MySQL  # pip install flask-mysql
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import re


app = Flask(__name__)
CORS(app, supports_credentials=True)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'cairocoders-ednalan'

mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'The11legende'
app.config['MYSQL_DATABASE_DB'] = 'perisco'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_PORT'] = 3306
mysql.init_app(app)


# http://localhost:5000/login/ - this will be the login page
@app.route('/login', methods=['POST'])
def login():
    # connect
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    data = request.get_json()

    # Check if "email" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in data and 'password' in data:
        # Create variables for easy access
        _email = data['email']
        _password = data['password']

        if _email and _password:
            # Check if account exists using MySQL
            cursor.execute('SELECT * FROM accounts WHERE email = %s', _email)
            # Fetch one record and return result
            account = cursor.fetchone()
            password = account['password']

            # If account exists in accounts table in out database
            if account:
                if check_password_hash(password, _password):
                    # Create session data, we can access this data in other routes
                    session['loggedin'] = True
                    session['id'] = account['account_id']
                    session['firstname'] = account['firstname']
                    session['lastname'] = account['lastname']
                    session['email'] = account['email']
                    cursor.close()

                    response = {
                        'loggedin': True,
                        'id': account['account_id'],
                        'firstname': account['firstname'],
                        'lastname': account['lastname'],
                        'email': account['email']
                    }
                    # response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
                else:
                    response = jsonify({'message': 'Mot de passe invalide'})
                    response.status_code = 400
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
            return {'message': msg}


# http://localhost:5000/user - this will be the registration page
@app.route('/user', methods=['GET', 'POST'])
def register():
    # connect
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    data = request.get_json()
    # Output message if something goes wrong...
    msg = ''
    # Check if "lastname", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST':
        if 'lastname' in data and 'password' in data and 'email' in data:
            # Create variables for easy access
            firstname = data['firstname']
            lastname = data['lastname']
            password = generate_password_hash(data['password'])
            email = data['email']

            # Check if account exists using MySQL
            cursor.execute('SELECT * FROM accounts WHERE email = %s', email)
            account = cursor.fetchone()
            # If account exists show error and validation checks
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            elif not re.match(r'[A-Za-z0-9]+', firstname):
                msg = 'Firstname must contain only characters and numbers!'
            elif not re.match(r'[A-Za-z0-9]+', lastname):
                msg = 'Lastname must contain only characters and numbers!'
            elif not lastname or not password or not email:
                msg = 'Please fill out the form!'
            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s)', (firstname, lastname, email, password))
                conn.commit()
                msg = 'You have successfully registered!'
        else:
            msg = 'Form error'
    elif request.method == 'GET':
        if 'id' in request.args:
            userId = int(request.args['id'])
            # Check if account exists using MySQL
            cursor.execute('SELECT * FROM accounts WHERE id = %s', userId)
            user = cursor.fetchone()
            return jsonify(user)
        else:
            msg = "Error: No id field provided. Please specify an id."
    # Show registration form with message (if any)
    return jsonify(msg)


# http://localhost:5000/home - this will be the home page, only accessible for loggedin users
@app.route('/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return jsonify(session)
    # User is not loggedin redirect to login page
    return {'message': 'you must be log in to access'}


# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('firstname', None)
    session.pop('lastname', None)
    session.pop('email', None)
    # Redirect to login page
    return {'message': 'You have successfully log out!'}


# http://localhost:5000/profile - this will be the profile page, only accessible for loggedin users
@app.route('/profile')
def profile():
    # Check if account exists using MySQL
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor.execute('SELECT * FROM accounts WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return jsonify(account)
    # User is not loggedin redirect to login page
    return {'message': 'you must be log in to have account access'}


@app.route('/registers')
def registers():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute('SELECT * FROM accounts')
    accounts = cursor.fetchall()
    response = jsonify(accounts)
    response.headers.add('Access-Control-Allow-Origin', '*')

    return response


# http://localhost:5000/child - this will be the registration page
@app.route('/add_child', methods=['POST'])
def createChild():
    # connect
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    data = request.get_json()
    # Output message if something goes wrong...
    msg = ''
    # Check if "lastname", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST':
        if 'firstname' in data and 'lastname' in data:
            # Create variables for easy access
            firstname = data['firstname']
            lastname = data['lastname']
            user_id = data['user_id']

            # Check if account exists using MySQL
            sql = 'SELECT * FROM children WHERE firstname = %s AND lastname = %s'
            values = (firstname, lastname)
            cursor.execute(sql, values)
            child = cursor.fetchone()
            # If account exists show error and validation checks
            if child:
                msg = 'Child already registered!'
            elif not re.match(r'[A-Za-z0-9]+', firstname):
                msg = 'Firstname must contain only characters and numbers!'
            elif not re.match(r'[A-Za-z0-9]+', lastname):
                msg = 'Lastname must contain only characters and numbers!'
            elif not firstname or not lastname:
                msg = 'Please fill out the form!'
            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                cursor.execute('INSERT INTO children VALUES (NULL, %s, %s)', (firstname, lastname))
                child_id = cursor.lastrowid
                cursor.execute('INSERT INTO children_accounts VALUES (%s, %s)', (child_id, user_id))
                conn.commit()
                msg = 'You have successfully registered a child!'
        else:
            msg = 'Form error'
    elif request.method == 'GET':
        msg = "Request error"
    # Show registration form with message (if any)
    return jsonify(msg)


# http://localhost:5000/child - this will be the registration page
@app.route('/children/<user_id>', methods=['GET'])
def findChildByUserId(user_id):
    # connect
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    if user_id:
        # Check if account exists using MySQL
        sql = f"SELECT * FROM children join perisco.children_accounts " \
              f"ON children.child_id = children_accounts.child_id " \
              f"WHERE children_accounts.account_id = %s"
        cursor.execute(sql, user_id)
        children = cursor.fetchall()
        return jsonify(children)
    else:
        msg = 'no child registred'
        return jsonify(msg)

# http://localhost:5000/child - this will be the registration page
@app.route('/child/<child_id>', methods=['GET'])
def findChildById(child_id):
    # connect
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    if child_id:
        # Check if account exists using MySQL
        sql = f"SELECT * FROM children " \
              f"WHERE child_id = %s"
        cursor.execute(sql, child_id)
        child = cursor.fetchone()
        return jsonify(child)
    else:
        msg = 'no child registred'
        return jsonify(msg)

# http://localhost:5000/child - this will be the registration page
@app.route('/del_child/<child_id>', methods=['DELETE'])
def deleteChildById(child_id):
    # connect
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    if child_id:
        # Check if account exists using MySQL
        sql = f"DELETE FROM children WHERE child_id = %s"
        cursor.execute(sql, child_id)
        conn.commit()
        return jsonify("informations deleted")
    else:
        msg = 'no child registred'
        return jsonify(msg)


if __name__ == '__main__':
    app.run(debug=True)