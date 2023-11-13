from pymongo import MongoClient
import secrets
import bcrypt
from datetime import datetime, timedelta

client = MongoClient("mongo")
database = client['CSE312-Group-Project']
client_users = database['users']
client_posts = database['posts']
client_comments = database['comments']
client_id = database['id']
client_likes = database['likes']

auction_items = database['auction_items']
auction_id = database['auction_id']

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
        'likes': 0,  # Number of likes
        'users_liked': [],  # List of users who have liked the post
        '_id': get_next_id()  # Function to get the next post ID
    }
    client_posts.insert_one(post_data)                      #! inserts post into database
    
def get_posts():                                            #! gets all posts   
    posts = list(client_posts.find({}))         #! returns a list of posts
    return posts


#Auction 

def next_auction_id():
    idNumber = auction_id.find_one({})
    nextID = 0
    if idNumber:
        nextId =int(idNumber['last_id']) + 1
        auction_id.update_one({}, {"$set": {'last_id':nextId}})
        return nextId
    else:
        auction_id.insert_one({'last_id':1})
        return 1


def create_auction_item(title, description, price, imagepath, duration):
    # Calculate the end time by adding the duration to the current time
    duration_hours = int(duration)
    end_time = datetime.now() + timedelta(minutes=duration_hours)

    auction_item = {
        'title': title,
        'description': description,
        'price': price,
        'imagepath': imagepath,
        'current_bidder': "",
        '_id': next_auction_id(),
        "previous_bids": [],
        "end_time": end_time,
        "winner": "",
        "duration": duration,
    }
    auction_items.insert_one(auction_item)
    return auction_item['_id'] 




def update_bidder(auction_id, bidder, bid_price):
    # Retrieve the auction item
    auction_item = auction_items.find_one({'_id': auction_id})
    
    if auction_item:
        prev_bidder = auction_item['current_bidder']
        prev_price = auction_item['price']
        
        # Check if there was a previous bidder
        if prev_bidder:
            # Add the previous bidder to the previous_bids list
            auction_items.update_one({'_id': auction_id}, {'$push': {'previous_bids': {'bidder': prev_bidder, 'price': prev_price}}})
        
        else:
            # Add the starting price to the previous_bids list
            auction_items.update_one({'_id': auction_id}, {'$push': {'previous_bids': {'bidder': 'Starting Price', 'price': prev_price}}})

        # Update the current bidder and the current price, regardless of whether there was a previous bidder
        auction_items.update_one({'_id': auction_id}, {'$set': {'current_bidder': bidder, 'price': bid_price}})


#! ______________________________ bid creator _________________________________________

def get_user_auctions(username):
    # Retrieve all auction items created by a specific user
    user_auctions = auction_items.find({'creator_username': username})
    return list(user_auctions)

#! ______________________________ bid winner _________________________________________

def list_auction_winners():
    # Retrieve all auction items that have a winner
    finished_auctions = auction_items.find({'winner': {'$ne': ""}})

    winners_list = []
    for auction in finished_auctions:
        winners_list.append({
            'username': auction['winner'],
            'item': auction['title'],
            'finalPrice': auction['price']
        })

    return winners_list

def get_auction_items():
    print(auction_items.find())
    return list(auction_items.find())


def get_auction_winner(auction_id):
    #- Retrieve the auction item using its ID
    auction_item = auction_items.find_one({'_id': auction_id})
    if auction_item and 'winner' in auction_item:
        return {
            'auction_id': auction_id,
            'username': auction_item['winner'],
            'item': auction_item['title'],
            'finalPrice': auction_item['price']
        }
    else:
        return None



