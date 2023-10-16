from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import secrets
from pymongo import MongoClient
import database as db

app = Flask(__name__)



@app.route("/")
def index():
    return render_template("index.html")


@app.route('/api/login', methods=['GET','POST'])
def login():
    data = request.get_json()
    if not data or 'credential' not in data:
        return jsonify({'error': 'email is required'}), 400
    credential = data['credential']
    # Check if the email exists in the database
    user = db.client_users.find_one({
        '$or': [
            {'email': credential},
            {'username': credential}
        ]
    })
    # If the user is not found in the database
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    else:
        # Generate a JWT token for the user and return it
        token = secrets.token_hex(16)
        return jsonify({'token': token}), 200  # Added 200 response code here

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    email = data['email']
    existUser = db.client_users.find_one({'email': email})
    if existUser:
        return jsonify({'error' : 'existing email in use'}), 400
    username = data.get('username')
    password = data.get('password')  
    new_user = {
        'email': email,
        'username': username,
        'password': password
    }
    db.client_users.insert_one(new_user)
    token = secrets.token_hex(16)
    return jsonify({'token': token}), 200 

