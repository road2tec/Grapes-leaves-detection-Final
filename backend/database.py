"""
============================================
Grapevine Disease Detection - Database Module
============================================

This module handles all MongoDB database operations including:
  - Database connection management
  - User CRUD operations (Create, Read)
  - Prediction history storage and retrieval

MongoDB Collections:
  - users: Stores registered user accounts
  - predictions: Stores disease prediction results

Connection: mongodb://localhost:27017/Grapevine_Disease
"""

from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId


import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "Grapevine_Disease")


def get_database():
    """
    Establish connection to MongoDB and return the database object.
    
    Creates a new MongoClient connection each time to ensure
    thread safety in the Flask web application.
    
    Returns:
        pymongo.database.Database: The Grapevine_Disease database
    """
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db


def get_users_collection():
    """
    Get the 'users' collection from the database.
    
    Users collection schema:
    {
        _id: ObjectId (auto-generated),
        name: str,
        email: str (unique),
        password: str (bcrypt hashed),
        created_at: datetime
    }
    
    Returns:
        pymongo.collection.Collection: The users collection
    """
    db = get_database()
    return db['users']


def get_predictions_collection():
    """
    Get the 'predictions' collection from the database.
    
    Predictions collection schema:
    {
        _id: ObjectId (auto-generated),
        user_id: str (references users._id),
        image_path: str (path to uploaded image),
        prediction: str (disease name),
        confidence: float (confidence percentage),
        all_predictions: dict (probabilities for all classes),
        date: datetime
    }
    
    Returns:
        pymongo.collection.Collection: The predictions collection
    """
    db = get_database()
    return db['predictions']


def create_user(name, email, hashed_password):
    """
    Create a new user in the database.
    
    Args:
        name (str): User's full name
        email (str): User's email address (must be unique)
        hashed_password (str): Bcrypt-hashed password
    
    Returns:
        str: The inserted user's ObjectId as a string
    """
    users = get_users_collection()
    
    user_doc = {
        'name': name,
        'email': email,
        'password': hashed_password,
        'created_at': datetime.utcnow()
    }
    
    result = users.insert_one(user_doc)
    return str(result.inserted_id)


def find_user_by_email(email):
    """
    Find a user by their email address.
    
    Used during login to verify credentials and during
    registration to check for duplicate emails.
    
    Args:
        email (str): Email address to search for
    
    Returns:
        dict or None: User document if found, None otherwise
    """
    users = get_users_collection()
    return users.find_one({'email': email})


def find_user_by_id(user_id):
    """
    Find a user by their MongoDB ObjectId.
    
    Used to verify JWT tokens and retrieve user info
    for authenticated routes.
    
    Args:
        user_id (str): User's ObjectId as a string
    
    Returns:
        dict or None: User document if found, None otherwise
    """
    users = get_users_collection()
    return users.find_one({'_id': ObjectId(user_id)})


def save_prediction(user_id, image_path, prediction, confidence, all_predictions=None):
    """
    Save a disease prediction result to the database.
    
    Called after each successful image prediction to build
    the user's prediction history for the dashboard.
    
    Args:
        user_id (str): ID of the user who made the prediction
        image_path (str): Path to the uploaded image file
        prediction (str): Predicted disease name
        confidence (float): Confidence percentage (0-100)
        all_predictions (dict, optional): Probabilities for all classes
    
    Returns:
        str: The inserted prediction's ObjectId as a string
    """
    predictions = get_predictions_collection()
    
    prediction_doc = {
        'user_id': user_id,
        'image_path': image_path,
        'prediction': prediction,
        'confidence': confidence,
        'all_predictions': all_predictions or {},
        'date': datetime.utcnow()
    }
    
    result = predictions.insert_one(prediction_doc)
    return str(result.inserted_id)


def get_user_predictions(user_id, limit=20):
    """
    Retrieve prediction history for a specific user.
    
    Returns the most recent predictions first, limited to
    a specified number for dashboard display.
    
    Args:
        user_id (str): User's ID to fetch predictions for
        limit (int): Maximum number of predictions to return (default: 20)
    
    Returns:
        list: List of prediction documents, newest first
    """
    predictions = get_predictions_collection()
    
    # Query predictions for this user, sorted by date (newest first)
    cursor = predictions.find(
        {'user_id': user_id}
    ).sort('date', -1).limit(limit)
    
    # Convert cursor to list and ObjectIds to strings for JSON serialization
    results = []
    for pred in cursor:
        pred['_id'] = str(pred['_id'])
        pred['date'] = pred['date'].strftime('%Y-%m-%d %H:%M:%S')
        results.append(pred)
    
    return results


def init_database():
    """
    Initialize the database with required indexes.
    
    Creates:
      - Unique index on users.email to prevent duplicate registrations
      - Index on predictions.user_id for fast history queries
    
    Should be called once when the application starts.
    """
    db = get_database()
    
    # Ensure email uniqueness for user accounts
    db['users'].create_index('email', unique=True)
    
    # Index on user_id for fast prediction history queries
    db['predictions'].create_index('user_id')
    
    # Index on prediction date for sorted queries
    db['predictions'].create_index('date')
    
    print("[INFO] Database indexes initialized successfully!")
