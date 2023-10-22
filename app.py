from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import secrets
from pymongo import MongoClient
import database as db
import bcrypt

from database import create_post, get_posts                 #! Post functions

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        data = request.form 
        username = data['username']
        password = data['password']
        user = db.client_users.find_one({'username':username})
        if user is None:
            return jsonify({'error' : 'invalid username'}), 400
        if bcrypt.hashpw(password.encode('utf-8'), user['salt']) == user['password']:
            auth = secrets.token_hex(16)
            db.client_users["auth"] = auth
            return redirect(url_for('index'))
        else:
            return jsonify({'error' : 'invalid password'}), 400
    


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        data = request.form
        username = data['username']
        password = data['password']
        if username is None or password is None:
            return jsonify({'error' : 'missing username or password'}), 400
        salt = bcrypt.gensalt()
        hashpassword = bcrypt.hashpw(password.encode('utf-8'), salt)
        db.register_user(username, hashpassword, salt)
        return jsonify({'success' : 'user created'}), 200


#!__________________________________________ POSTS ____________________________________________!#

@app.route('/post', methods=['POST'])
def create_post_route():
    username = request.form['username']
    title = request.form['title']                   
    description = request.form['description']      
    
    if not (username and title and description):        #! checks if all fields are filled
        return jsonify({'error': 'Missing data'}), 400
    
    create_post(username, title, description)           #! creates a post
    return jsonify({'success': True})                   #! returns a json string



@app.route('/posts', methods=['GET'])
def fetch_posts():
    posts = get_posts()                                 #! gets all posts   
    return jsonify(posts), 200

#!__________________________________________ POSTS Ending ____________________________________________!#




if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)