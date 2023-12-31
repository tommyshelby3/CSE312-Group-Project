from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    make_response,
)
import secrets
from pymongo import MongoClient
import database as db
import bcrypt
from html import escape
from database import create_post, get_posts  #! Post functions
from flask_socketio import SocketIO
from flask_socketio import send, emit, join_room, leave_room
from flask import Blueprint, render_template, session
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
from flask_login import current_user
from werkzeug.utils import secure_filename
import auction
import os
from threading import Thread
import time
from flask_mail import Mail, Message

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import googleapiclient.errors
from email.mime.text import MIMEText
import base64
from dotenv import load_dotenv
# from your_auction_model import Auction
from database import *
import eventlet
import hashlib
import requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "./static/images"
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

# Define the scope of the application
scopes = ['https://www.googleapis.com/auth/gmail.send']
# Disable OAuthlib's HTTPS verification when running locally.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

client_id = os.environ.get('GMAIL_API_CLIENT_ID')
client_secret = os.environ.get('GMAIL_API_CLIENT_SECRET')


HOSTNAME = "http://localhost:8080"


def gmail_send_message(sender, to, subject, body_text):
    """Send an email message using the Gmail API.

    Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        body_text: The body text of the email message.
    """
    creds = None

    token_file = os.environ.get('GMAIL_API_TOKEN')
    credentials_file = os.environ.get('GMAIL_API_CREDENTIALS')

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, scopes=scopes )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)

        # Create a MIMEText object for the email message
        message = MIMEText(body_text)
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        # Encode the message string into bytes and then base64 for the Gmail API
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create the message body for the API request
        create_message = {'raw': encoded_message}

        # Call the Gmail API to send the email
        send_message = service.users().messages().send(
            userId="me", body=create_message).execute()
        print(f"Message Id: {send_message['id']}")
        return send_message
    except Exception as error:
        print(f"An error occurred: {error}")
        return None



# Initialize Flask-Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[]  # Disable global limits
)
# This dictionary will keep track of blocked IPs with expiration times
blocked_ips = {}

@app.before_request
def check_ip_block():
    # Get the requester's IP address
    ip = get_remote_address()

    # Check if the IP is blocked
    if is_ip_blocked(ip):
        # If blocked, return a custom 429 response
        return jsonify(error="Too Many Requests", message="Your IP is temporarily blocked due to excessive requests."), 429
    # If not blocked, proceed with the request

def is_ip_blocked(ip):
    if ip in blocked_ips:
        block_time = blocked_ips[ip]
        if datetime.now() < block_time:
            return True
    # If the block has expired, remove the IP from the blocked list
    blocked_ips.pop(ip, None)  # Removes the IP if it's present, does nothing otherwise
    return False


def block_ip(ip, duration=30):
    # Block the IP for the given duration (in seconds)
    blocked_ips[ip] = datetime.now() + timedelta(seconds=duration)


@app.errorhandler(429)
def ratelimit_handler(e):
    ip = get_remote_address()
    block_ip(ip, duration=30)  # Block the IP for 30 seconds
    return jsonify(
        error="Too Many Requests", message="You have exceeded the rate limit. Please wait 30 seconds before trying again."
    ), 429


@app.route("/")
@limiter.limit("50 per 10 seconds")
def index():
    auth = request.cookies.get("auth")
    if auth is None:
        return render_template("index.html", username="Guest")
    else:
        user = db.client_users.find_one({"auth": auth})
        print(user)
        winners = list_auction_winners()
        if user is None:
            return redirect(url_for("login"))
        else:
            return render_template(
                "index.html", username=user["username"], winners=winners
            )


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("50 per 10 seconds")
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        data = request.form
        username = data["username"]
        password = data["password"]
        user = db.client_users.find_one({"username": username})
        if user is None:
            return jsonify({"error": "invalid username"}), 400
        if bcrypt.hashpw(password.encode("utf-8"), user["salt"]) == user["password"]:
            auth = secrets.token_hex(16)

            auth = hashlib.sha256(auth.encode("utf-8")).hexdigest()
            print(auth)
            db.client_users.update_one({"username": username}, {"$set": {"auth": auth}})
            response = make_response(redirect(url_for("index")))
            response.set_cookie("auth", auth, httponly=True, max_age=3600)
            return response
        else:
            return jsonify({"error": "invalid password"}), 400


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("50 per 10 seconds")
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        data = request.form
        username = data["username"]
        password = data["password"]
        email = data['email']

        # Basic validation for input
        if not username or not password or not email:
            flash('Missing username, password, or email', 'error')
            return render_template("register.html")

        # Check if username or email already exists
        # Assuming this function exists in your db module
        if db.user_exists(username, email):
            flash('Username or email already exists', 'error')
            return render_template("register.html")

        # Password hashing
        salt = bcrypt.gensalt()
        hashpassword = bcrypt.hashpw(password.encode("utf-8"), salt)

        # Register user and get verification token
        token = db.register_user(username, hashpassword, salt, email)

        # Construct the email verification URL
        verify_url = url_for('verify_email', token=token, _external=True)
        print(verify_url)

        # Send verification email using Gmail API
        subject = 'Email Verification'
        body_text = f'Please click on the following link to verify your email: {verify_url}'
        gmail_send_message('bot.app.board@gmail.com', email, subject, body_text)

        flash('Please check your email to verify your account', 'info')
        return redirect(url_for("profile"))

@app.route("/verify_email", methods=["GET"])
@limiter.limit("50 per 10 seconds")
def verify_email_page():
    auth = request.cookies.get("auth")
    if auth is None:
        return redirect(url_for("login"))
    else:
        user = db.client_users.find_one({"auth": auth})
        if user is None:
            return redirect(url_for("login"))
        db.client_users.update_one({"username": user["username"]}, {"$set": {"email_verified": True}})
        return render_template("verify_email.html")

@app.route('/verify_email/<token>')
def verify_email(token):
    if db.verify_email(token):
        flash('Your email has been verified!', 'success')
        return redirect(url_for('profile'))
    else:
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('register'))
    

@app.route('/resend_verification_email', methods=['POST'])
def resend_verification_email():
    email = request.form.get('email')
    flash('Verification email resent to ' + email, 'info')
    return redirect(url_for('profile'))  # Redirect back to the profile page


#!__________________________________________ POSTS ____________________________________________!#


@app.route("/post", methods=["POST"])
@limiter.limit("50 per 10 seconds")
def create_post_route():
    auth = request.cookies.get("auth")
    if not auth:
        return jsonify({"error": "Log in to create a post"}), 403
    user = db.client_users.find_one({"auth": auth})
    if not user:
        return jsonify({"error": "Invalid authentication token"}), 400
    username = escape(user["username"])
    title = escape(request.form["title"])
    description = escape(request.form["description"])
    create_post(username, title, description)
    return jsonify({"success": True})


@app.route("/posts", methods=["GET"])
@limiter.limit("50 per 10 seconds")
def fetch_posts():
    posts = get_posts()  #! gets all posts
    return jsonify(posts), 200


@app.route("/posts/like/<int:post_id>", methods=["POST"])
@limiter.limit("50 per 10 seconds")
def update_like(post_id):
    auth = request.cookies.get("auth")
    if not auth:
        return jsonify({"error": "Log in to like a post"}), 403
    user = db.client_users.find_one({"auth": auth})
    if not user:
        return jsonify({"error": "Invalid authentication token"}), 400
    # Check if the post exists
    post = db.client_posts.find_one({"_id": post_id})
    if not post:
        return jsonify({"error": "Post not found"}), 404

    username = user["username"]  # unique identifier for the user in this case
    post_username = post["username"]

    liked = db.client_likes.find_one(
        {"_id": post_id, "username": username, "post_username": post_username}
    )
    if liked:
        db.client_posts.update_one({"_id": post_id}, {"$inc": {"likes": -1}})
        db.client_likes.delete_one(
            {"_id": post_id, "username": username, "post_username": post_username}
        )
    else:
        db.client_posts.update_one({"_id": post_id}, {"$inc": {"likes": 1}})
        db.client_likes.insert_one(
            {"_id": post_id, "username": username, "post_username": post_username}
        )
    return jsonify({"success": True})


#!__________________________________________ Auction ____________________________________________!#


@app.route("/auction", methods=["GET", "POST"])
@limiter.limit("50 per 10 seconds")
def auction_page():
    if request.method == "GET":
        auction_items = db.get_auction_items()
        list_auction = []
        for item in auction_items:
            socket_auction = {
                "title": item["title"],
                "description": item["description"],
                "price": item["price"],
                "imagepath": item["imagepath"],
                "duration": item["duration"],
            }
            list_auction.append(socket_auction)
        socketio.emit("update_items", list_auction, namespace="/auction")
        return render_template("auction.html", auction_items=auction_items)
    elif request.method == "POST":
        return redirect(url_for("post"))


@app.route("/profile", methods=["GET"])
@limiter.limit("50 per 10 seconds")
def profile():
    auth = request.cookies.get("auth")
    if not auth:
        return jsonify({"error": "Log in to create a post"}), 403
    user = db.client_users.find_one({"auth": auth})
    if not user:
        return jsonify({"error": "Invalid authentication token"}), 400
    username = escape(user["username"])
    return redirect(url_for("profile_page", username=username))


@app.route("/profile/<username>", methods=["GET"])
@limiter.limit("50 per 10 seconds")
def profile_page(username):
    user_posts = db.get_user_auctions(username)
    auction_items = db.get_user_auctions_wins(username)
    print(auction_items)
    print(user_posts)
    return render_template(
        "profile.html", username=username, posts=user_posts, wins=auction_items
    )


@app.route("/post", methods=["GET", "POST"])
@limiter.limit("50 per 10 seconds")
def auction_upload():
    if request.method == "GET":
        return render_template("post.html")
    elif request.method == "POST":
        data = request.form
        title = data["title"]
        description = data["description"]
        price = data["price"]
        # auction = Auction(title, description, price)
        # auction.upload_auction_item()
        return redirect(url_for("auction_page"))


@app.route("/auctions/create", methods=["POST"])
@limiter.limit("50 per 10 seconds")
def create_auction():
    auctionItem = auction.Auction(
        request.form["title"], request.form["description"], request.form["price"], ""
    )
    image_path = app.config["UPLOAD_FOLDER"] + auctionItem.auction_id + ".jpg"
    auctionItem.imagepath = image_path
    request.files["image"].save(image_path)
    return redirect(url_for("auction"))


@app.route("/upload_auction", methods=["GET", "POST"])
@limiter.limit("50 per 10 seconds")
def upload_auction():
    if request.method == "POST":
        # - check if user is logged in
        auth = request.cookies.get("auth")
        if not auth:
            flash("You must be logged in to create an auction.")
            return redirect(url_for("login"))

        user = db.client_users.find_one({"auth": auth})
        if not user:
            flash("Invalid authentication token.")
            return redirect(url_for("login"))

        username = user["username"]

        # - process the uploaded file and form data
        title = request.form["title"]
        description = request.form["description"]
        starting_price = request.form["starting_price"]
        # - process the duration appropriately
        duration = request.form["duration"]
        image = request.files["image"]

        image_path = "./static/images/"
        if not os.path.exists(image_path):
            os.makedirs(image_path)

        image_filename = secure_filename(image.filename)
        image.save(os.path.join(image_path, image_filename))

        # - save the action item to the database
        db.create_auction_item(
            title, description, starting_price, image_filename, duration, username
        )

        # - redirect to the auction house page
        socketio.emit("auction_items", db.get_auction_items())
        return redirect(url_for("auction_page"))
    else:
        # - If it's a GET request, just render the upload auction form
        return render_template("upload_auction.html")


def upload_auction_item():
    return jsonify({"success": "Auction item uploaded successfully."})


@socketio.on("bid", namespace="/auction")
@limiter.limit("50 per 10 seconds")
def handle_bid(json):
    # Authentication check
    auth = request.cookies.get("auth")
    if not auth:
        emit("error", {"error": "Authentication required"})
        return
    user = db.client_users.find_one({"auth": auth})
    if not user:
        emit("error", {"error": "Invalid authentication token"})
        return

    # Extract bid information from json
    auction_id = int(json["auction_id"])
    bid_amount = json["bid_amount"]

    username = user["username"]
    auctionCreator = db.auction_items.find_one({"_id": int(auction_id)})[
        "creator_username"
    ]
    if username == auctionCreator:
        emit("error", {"error": "You cannot bid on your own auction"})
        return
    # Fetch the auction item
    print(db.auction_items)
    auction_item = db.auction_items.find_one({"_id": int(auction_id)})

    # Check if the auction is still active and the bid is valid
    if (
        auction_item
        and auction_item["end_time"] > datetime.now()
        and bid_amount > auction_item["price"]
    ):
        print("Bid is valid")
        # Update the bid
        db.update_bidder(auction_id, user["username"], bid_amount)
        # Emit the new bid to all clients
        emit(
            "new_bid",
            {"auction_id": auction_id, "new_price": bid_amount},
            broadcast=True,
            namespace="/auction",
        )
    else:
        emit(
            "error",
            {"error": "Bid is not valid or auction has ended"},
            namespace="/auction",
        )


# Websocket for Auction
@socketio.on("message")
@limiter.limit("50 per 10 seconds")
def handleMessage(msg):
    print("Message: " + msg)
    send(msg, broadcast=True)


@socketio.on("connect", namespace="/auction")
@limiter.limit("50 per 10 seconds")
def handleConnect():
    print("Client connected to regular WS")
    db.print_auctions()
    emit("my response", {"data": "Connected"})


def broadcast_time_remaining():
    print("Starting background thread")
    while True:
        auction_items = db.get_auction_items()
        for item in auction_items:
            time_remaining = item["end_time"] - datetime.now()
            if time_remaining.total_seconds() > 0:
                socketio.emit(
                    "time_remaining_update",
                    {"auction_id": item["_id"], "time_remaining": str(time_remaining)},
                    namespace="/auction",
                )
            else:
                db.auction_items.update_one(
                    {"_id": item["_id"]}, {"$set": {"winner": item["current_bidder"]}}
                )
                socketio.emit(
                    "time_remaining_update",
                    {"auction_id": item["_id"], "time_remaining": str("auction ended")},
                    namespace="/auction",
                )
        eventlet.sleep(1)  # Update every minute, adjust as needed


#! ______________________________________ Bid creator ______________________________________ !#


@app.route("/bid_creator")
@limiter.limit("50 per 10 seconds")
def bid_creator():
    if "username" in session:
        user_auctions = get_user_auctions(session["username"])
        return render_template("bid_creator.html", auctions=user_auctions)
    else:
        return "Please login to view this page", 403


#! ______________________________________ Bid winner ______________________________________ !#
@socketio.on("request_auction_winners")
@limiter.limit("50 per 10 seconds")
def auction_winners():
    winners = list_auction_winners()
    return list(winners)


@socketio.on("auction_winner")
@limiter.limit("50 per 10 seconds")
def auction_winner():
    winner = get_auction_winner()
    print(winner)
    return winner


@socketio.on("connect")
@limiter.limit("50 per 10 seconds")
def handle_connect():
    print("Client connected to regular WS")
    winner = list_auction_winners()
    print(winner)
    emit("auction_winner", winner)


@socketio.on("request_auction_winners")
@limiter.limit("50 per 10 seconds")
def handle_request_auction_winners():
    print("Client requested auction winners")
    auction_items = get_auction_items()
    for item in auction_items:
        if item["end_time"] < datetime.now():
            winner_data = get_auction_winner(item["_id"])
            if winner_data:
                emit("auction_winner", winner_data)


@socketio.on("auction_ended")
@limiter.limit("50 per 10 seconds")
def handle_auction_ended(auction_id):
    winner = get_auction_winner(auction_id)
    print(winner)
    emit(
        "auction_winner",
        {
            "username": winner["username"],
            "item": winner["item"],
            "finalPrice": winner["finalPrice"],
        },
    )


def emit_auction_winner(auction_id):
    winner_details = get_auction_winner(auction_id)
    if winner_details:
        emit("auction_winner", winner_details, broadcast=True)


if __name__ == "__main__":
    app.secret_key = "super secret key"
    socketio.start_background_task(broadcast_time_remaining)
    socketio.run(app, host="0.0.0.0", port=8080, debug=True, use_reloader=False)
