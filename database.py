from pymongo import MongoClient
import secrets
import bcrypt

client = MongoClient('localhost', 27017)
db = client['CSE312-Group-Project']
