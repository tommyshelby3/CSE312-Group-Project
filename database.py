from pymongo import MongoClient
import secrets
import bcrypt

client = MongoClient("mongo")
database = client['CSE312-Group-Project']
client_users = database['users']
client_posts = database['posts']
client_comments = database['comments']
client_id = database['id']

def get_next_id():
    idNumber = client_id.find_one({})
    nextID = 0
    if idNumber:
        nextId =int(idNumber['last_id']) + 1
        client_id.update_one({}, {"$set": {'last_id':nextId}})
        return nextId
    else:
        client_id.insert_one({'last_id':1})
        return 1

def register_user(username, password, salt):
    new_user = {
        'username': username,
        'password': password,
        'salt': salt,
        'auth': None,
        '_id': get_next_id()
    }
    client_users.insert_one(new_user)

def create_post(username, title, description):              #! creates a post
    post_data = {
        'username': username,
        'title': title,
        'description': description,
        'likes': 0,
        '_id': get_next_id()
    }
    client_posts.insert_one(post_data)                      #! inserts post into database
    
def get_posts():                                            #! gets all posts   
    posts = list(client_posts.find({}))         #! returns a list of posts
    return posts