"""
============================================
Grapevine Disease Detection - Flask Backend
============================================

Main application file that provides the REST API and serves
the web frontend for the Grapevine Disease Detection System.

Endpoints:
  - GET  /                  → Home page
  - GET  /login             → Login page
  - GET  /register          → Registration page
  - GET  /dashboard         → Prediction history dashboard
  - GET  /predict-page      → Disease prediction page
  - POST /register          → Register new user
  - POST /login             → Authenticate user
  - POST /predict           → Upload image and predict disease
  - GET  /api/history       → Get prediction history (JSON)
  - GET  /uploads/<file>    → Serve uploaded images

All protected routes require JWT authentication.
"""

import os
import sys
from datetime import datetime
from flask import (
    Flask, request, jsonify, render_template,
    send_from_directory, redirect, url_for
)
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add parent and sibling directories to Python path for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))
sys.path.insert(0, os.path.join(BASE_DIR, 'model'))

# Import project modules
from auth import hash_password, verify_password, generate_token, token_required
from database import (
    create_user, find_user_by_email,
    save_prediction, get_user_predictions, init_database
)
from predict import predict_disease


# ============================================
# Flask App Configuration
# ============================================
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'frontend'),    # HTML templates
    static_folder=os.path.join(BASE_DIR, 'static'),         # Static assets (CSS, JS)
)

# Enable Cross-Origin Resource Sharing for API endpoints
CORS(app)

# File upload configuration
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """
    Check if the uploaded file has an allowed image extension.
    
    Prevents users from uploading non-image files that could
    cause errors or security issues.
    
    Args:
        filename (str): Name of the uploaded file
    
    Returns:
        bool: True if file extension is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================
# Page Routes (Serve HTML Templates)
# ============================================

@app.route('/')
def home():
    """Serve the home/landing page."""
    return render_template('index.html')


@app.route('/login')
def login_page():
    """Serve the login page."""
    return render_template('login.html')


@app.route('/register')
def register_page():
    """Serve the registration page."""
    return render_template('register.html')


@app.route('/dashboard')
def dashboard_page():
    """
    Serve the prediction history dashboard.
    Authentication is handled client-side via JWT.
    """
    return render_template('dashboard.html')


@app.route('/predict-page')
def predict_page():
    """
    Serve the disease prediction page.
    Authentication is handled client-side via JWT.
    """
    return render_template('predict.html')


# ============================================
# API Routes - Authentication
# ============================================

@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    Expected JSON body:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "securepassword"
    }
    
    Process:
      1. Validate input fields
      2. Check if email already exists
      3. Hash the password with bcrypt
      4. Save user to MongoDB
      5. Return success response
    
    Returns:
        JSON response with success status and message
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not name or not email or not password:
            return jsonify({
                'success': False,
                'message': 'All fields are required (name, email, password).'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 6 characters long.'
            }), 400
        
        # Check if user already exists
        existing_user = find_user_by_email(email)
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'An account with this email already exists.'
            }), 409
        
        # Hash password and create user
        hashed_pw = hash_password(password)
        user_id = create_user(name, email, hashed_pw)
        
        # Generate JWT token for immediate login after registration
        token = generate_token(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! Welcome aboard.',
            'token': token,
            'user': {
                'id': user_id,
                'name': name,
                'email': email
            }
        }), 201
        
    except Exception as e:
        print(f"[ERROR] Registration failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Registration failed. Please try again.'
        }), 500


@app.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user and return a JWT token.
    
    Expected JSON body:
    {
        "email": "john@example.com",
        "password": "securepassword"
    }
    
    Process:
      1. Find user by email in MongoDB
      2. Verify password against bcrypt hash
      3. Generate JWT token on success
      4. Return token for client-side storage
    
    Returns:
        JSON response with token on success, error on failure
    """
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required.'
            }), 400
        
        # Find user in database
        user = find_user_by_email(email)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid email or password.'
            }), 401
        
        # Verify password against stored hash
        if not verify_password(password, user['password']):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password.'
            }), 401
        
        # Generate JWT token for authenticated session
        user_id = str(user['_id'])
        token = generate_token(user_id)
        
        return jsonify({
            'success': True,
            'message': f'Welcome back, {user["name"]}!',
            'token': token,
            'user': {
                'id': user_id,
                'name': user['name'],
                'email': user['email']
            }
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Login failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Login failed. Please try again.'
        }), 500


# ============================================
# API Routes - Disease Prediction
# ============================================

@app.route('/predict', methods=['POST'])
@token_required
def predict(current_user):
    """
    Upload a grape leaf image and predict the disease.
    
    Requires JWT authentication (token in header/form).
    
    Expected: multipart/form-data with 'image' file field
    
    Process:
      1. Validate uploaded file
      2. Save image to uploads directory
      3. Run CNN model prediction
      4. Save result to MongoDB
      5. Return prediction results
    
    Args:
        current_user (dict): Authenticated user from JWT decorator
    
    Returns:
        JSON with disease name, confidence, and all class probabilities
    """
    try:
        # Check if image file was included in request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No image file provided. Please upload an image.'
            }), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected. Please choose an image.'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'Invalid file type. Please upload PNG, JPG, JPEG, GIF, BMP, or WEBP.'
            }), 400
        
        # Save the uploaded file with a unique name
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        print(f"[INFO] Image saved: {filepath}")
        
        # Run disease prediction using the trained CNN model
        result = predict_disease(filepath)
        
        # Save prediction to database for history tracking
        save_prediction(
            user_id=current_user['_id'],
            image_path=unique_filename,
            prediction=result['disease_name'],
            confidence=result['confidence'],
            all_predictions=result['all_predictions']
        )
        
        return jsonify({
            'success': True,
            'prediction': result['disease_name'],
            'confidence': result['confidence'],
            'all_predictions': result['all_predictions'],
            'image_url': f'/uploads/{unique_filename}'
        }), 200
        
    except FileNotFoundError as e:
        return jsonify({
            'success': False,
            'message': f'Model not found. Please train the model first. Error: {str(e)}'
        }), 500
    except Exception as e:
        print(f"[ERROR] Prediction failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Prediction failed: {str(e)}'
        }), 500


# ============================================
# API Routes - Prediction History
# ============================================

@app.route('/api/history', methods=['GET'])
@token_required
def get_history(current_user):
    """
    Retrieve the authenticated user's prediction history.
    
    Returns the most recent 20 predictions with disease names,
    confidence scores, and image paths.
    
    Args:
        current_user (dict): Authenticated user from JWT decorator
    
    Returns:
        JSON array of prediction records
    """
    try:
        predictions = get_user_predictions(current_user['_id'])
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'total': len(predictions)
        }), 200
        
    except Exception as e:
        print(f"[ERROR] History retrieval failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve prediction history.'
        }), 500


# ============================================
# Static File Routes
# ============================================

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Serve uploaded images from the uploads directory.
    
    Used by the frontend to display uploaded leaf images
    in prediction results and dashboard history.
    
    Args:
        filename (str): Name of the uploaded file
    
    Returns:
        File response with the requested image
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files from the frontend directory."""
    return send_from_directory(os.path.join(BASE_DIR, 'frontend'), filename)


# ============================================
# Application Entry Point
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("  🍇 Grapevine Disease Detection System")
    print("=" * 60)
    
    # Initialize database indexes
    try:
        init_database()
        print("[✓] Database connected and initialized")
    except Exception as e:
        print(f"[!] Database warning: {str(e)}")
        print("    Make sure MongoDB is running on localhost:27017")
    
    # Check if the trained model exists
    model_path = os.path.join(BASE_DIR, 'model', 'grape_disease_model.h5')
    if os.path.exists(model_path):
        print(f"[✓] Trained model found: {model_path}")
    else:
        print(f"[!] Model not found: {model_path}")
        print("    Run 'python model/model_training.py' to train the model first.")
    
    print(f"\n  Starting server at: http://localhost:5000")
    print(f"  Press Ctrl+C to stop\n")
    print("=" * 60)
    
    # Start Flask development server
    app.run(
        host='0.0.0.0',    # Accept connections from any IP
        port=5000,          # Run on port 5000
        debug=True          # Enable debug mode for development
    )
