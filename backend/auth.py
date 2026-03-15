"""
============================================
Grapevine Disease Detection - Authentication Module
============================================

This module provides user authentication functionality:
  - Password hashing using bcrypt
  - JWT (JSON Web Token) generation and verification
  - Route protection decorator for secured endpoints

Security Features:
  - Passwords are hashed with bcrypt (never stored in plaintext)
  - JWT tokens expire after 24 hours
  - Protected routes require valid JWT in request header
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

# Import database functions for user lookup
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import find_user_by_id


from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# ============================================
# Configuration
# ============================================
# Secret key for JWT token encoding/decoding
# In production, this should be stored in environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "grapevine_disease_detection_secret_key_2024")

# Token expiration time (24 hours)
TOKEN_EXPIRY_HOURS = 24


def hash_password(password):
    """
    Hash a plaintext password using bcrypt.
    
    Bcrypt automatically generates a random salt and includes it
    in the hash, making each hash unique even for identical passwords.
    This protects against rainbow table attacks.
    
    Args:
        password (str): Plaintext password from user input
    
    Returns:
        str: Bcrypt-hashed password string
    """
    # Generate salt and hash the password
    # The salt factor (rounds) is 12 by default, providing good security
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password, hashed_password):
    """
    Verify a plaintext password against a bcrypt hash.
    
    Used during login to check if the provided password
    matches the stored hash without ever decrypting the hash.
    
    Args:
        password (str): Plaintext password from login form
        hashed_password (str): Bcrypt hash from database
    
    Returns:
        bool: True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def generate_token(user_id):
    """
    Generate a JWT token for an authenticated user.
    
    The token contains:
      - user_id: The user's database ID
      - exp: Expiration timestamp (24 hours from now)
      - iat: Issued-at timestamp
    
    This token must be included in subsequent API requests
    to access protected endpoints.
    
    Args:
        user_id (str): The authenticated user's database ID
    
    Returns:
        str: Encoded JWT token string
    """
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def decode_token(token):
    """
    Decode and verify a JWT token.
    
    Checks that the token:
      - Has a valid signature (not tampered with)
      - Has not expired
    
    Args:
        token (str): JWT token string
    
    Returns:
        dict or None: Decoded payload if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired - user needs to login again
        return None
    except jwt.InvalidTokenError:
        # Token is invalid - possible tampering
        return None


def token_required(f):
    """
    Decorator to protect Flask routes with JWT authentication.
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route(current_user):
            # current_user contains the user document from MongoDB
            return jsonify({'message': f'Hello {current_user["name"]}'})
    
    The decorator:
      1. Extracts JWT from Authorization header or query parameter
      2. Decodes and validates the token
      3. Looks up the user in the database
      4. Passes the user object to the route function
    
    Args:
        f: The Flask route function to protect
    
    Returns:
        function: Wrapped function with authentication check
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header (Bearer token)
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Extract token after 'Bearer'
            except IndexError:
                token = auth_header
        
        # Also check for token in query parameters (for convenience)
        if not token:
            token = request.args.get('token')
        
        # Also check for token in form data
        if not token:
            token = request.form.get('token')
        
        # Also check for token in JSON body
        if not token and request.is_json:
            token = request.json.get('token')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication token is missing. Please login first.'
            }), 401
        
        # Decode and verify the token
        payload = decode_token(token)
        if payload is None:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token. Please login again.'
            }), 401
        
        # Look up the user in the database
        current_user = find_user_by_id(payload['user_id'])
        if current_user is None:
            return jsonify({
                'success': False,
                'message': 'User not found. Please register again.'
            }), 401
        
        # Convert ObjectId to string for JSON serialization
        current_user['_id'] = str(current_user['_id'])
        
        # Pass the user object to the protected route
        return f(current_user, *args, **kwargs)
    
    return decorated
