# from flask import Flask, request, jsonify
# from database import create_post, get_posts

# import secrets
# from pymongo import MongoClient
# import database as db

# app = Flask(__name__)

# @app.route('/post', methods=['POST'])
# def create_post_route():
#     username = request.form['username']
#     title = request.form['title']                   
#     description = request.form['description']      
    
#     if not (username and title and description):        #! checks if all fields are filled
#         return jsonify({'error': 'Missing data'}), 400
    
#     create_post(username, title, description)           #! creates a post
#     return jsonify({'success': True})                   #! returns a json string



# @app.route('/posts', methods=['GET'])
# def fetch_posts():
#     posts = get_posts()                                 #! gets all posts   
#     return jsonify(posts), 200