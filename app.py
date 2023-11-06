from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
import secrets
from pymongo import MongoClient
import database as db
import bcrypt
from html import escape
from database import create_post, get_posts                 #! Post functions
from flask_socketio import SocketIO
from flask_socketio import send, emit, join_room, leave_room


app = Flask(__name__)
socketio = SocketIO(app)


@app.route("/")
def index():
    auth = request.cookies.get('auth')
    if auth is None:
        return render_template("index.html", username = "Guest")
    else:
        user = db.client_users.find_one({'auth':auth})
        print(user)
        if user is None:
            return redirect(url_for('login'))
        else:
            return render_template("index.html", username=user['username'])
        


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
            db.client_users.update_one({'username':username}, {"$set": {'auth':auth}})
            response = make_response(redirect(url_for('index')))
            response.set_cookie('auth', auth, httponly = True, max_age = 3600)
            return response
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
        return redirect(url_for('index'))


#!__________________________________________ POSTS ____________________________________________!#

@app.route('/post', methods=['POST'])
def create_post_route():
    auth = request.cookies.get('auth')
    if not auth:
        return jsonify({'error': 'Log in to create a post'}), 403
    user = db.client_users.find_one({'auth': auth})
    if not user:
        return jsonify({'error': 'Invalid authentication token'}), 400
    username = escape(user['username'])
    title = escape(request.form['title'])
    description = escape(request.form['description'])
    create_post(username, title, description)
    return jsonify({'success': True})

@app.route('/posts', methods=['GET'])
def fetch_posts():
    posts = get_posts()                                 #! gets all posts   
    return jsonify(posts), 200

@app.route('/posts/like/<int:post_id>', methods=['POST'])
def update_like(post_id):
    auth = request.cookies.get('auth')
    if not auth:
        return jsonify({'error': 'Log in to like a post'}), 403
    user = db.client_users.find_one({'auth': auth})
    if not user:
        return jsonify({'error': 'Invalid authentication token'}), 400
    # Check if the post exists
    post = db.client_posts.find_one({'_id': post_id})
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    username = user['username']  # unique identifier for the user in this case
    post_username = post['username']
    
    liked = db.client_likes.find_one({'_id': post_id, 'username':username, 'post_username': post_username})
    if liked:
        db.client_posts.update_one({'_id': post_id}, {'$inc': {'likes': -1}})
        db.client_likes.delete_one({'_id': post_id, 'username':username, 'post_username': post_username})
    else:
        db.client_posts.update_one({'_id': post_id}, {'$inc': {'likes': 1}})
        db.client_likes.insert_one({'_id': post_id, 'username':username, 'post_username': post_username})
    return jsonify({'success': True})

#!__________________________________________ POSTS Ending ____________________________________________!#


#Websocket for Auction
@socketio.on('message')
def handleMessage(msg):
    print('Message: ' + msg)
    send(msg, broadcast=True)

@socketio.on('json')
def handleJson(json):
    print('json: ' + str(json))
    send(json, broadcast=True)

@socketio.on('my event')
def handleMyEvent(json):
    print('my event: ' + str(json))
    send(json, broadcast=True)

@socketio.on('connect')
def handleConnect():
    print('Client connected')






if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
    socketio.run(app)