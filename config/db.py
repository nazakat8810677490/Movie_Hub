from pymongo import MongoClient
import gridfs

MONGO_URI = "mongodb+srv://Herry:Herry%405%405@cluster0.ugnohw5.mongodb.net/"

client = MongoClient(MONGO_URI)

db = client["movie_hub"]

admins = db["admins"]
customers = db["customers"]
categories = db["categories"]
movies = db["movies"]