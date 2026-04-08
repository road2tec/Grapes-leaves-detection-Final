"""
============================================
Grapevine Disease Detection - Flask Backend
============================================

Main application file with all feature modules:
  Core: Home, Auth, Disease Prediction
  Module 1: Smart Advisor Chatbot (Gemini 2.0 Flash)
  Module 2: Govt Schemes + Carbon Credits
  Module 3: Mandi / Market Prices
  Module 4: Disease Recommendations
  Module 5: Community Forum (Farmer ↔ Consultant)
  Module 6: Equipment Marketplace (OLX-type)
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

# ============ New Feature Modules ============
from chatbot import send_message, get_chat_sessions, get_session_messages
from mandi_prices import get_prices, get_all_commodities
from schemes import get_schemes, get_carbon_credits, get_scheme_categories, init_schemes_data
from recommendation import get_recommendation
from forum import (
    create_thread, get_threads, get_thread_detail,
    add_reply, mark_solution, get_forum_stats, FORUM_CATEGORIES
)
from marketplace import (
    create_ad, get_ads, get_ad_detail, update_ad_status,
    delete_ad, get_user_ads, get_marketplace_stats, EQUIPMENT_CATEGORIES
)


# ============================================
# Flask App Configuration
# ============================================
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'frontend'),    # HTML templates
    static_folder=os.path.join(BASE_DIR, 'static'),         # Static assets (CSS, JS)
)
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
    """Register a new user account with role support (farmer/consultant)."""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', 'farmer').strip().lower()   # 'farmer' or 'consultant'
        phone = data.get('phone', '').strip()
        location = data.get('location', '').strip()
        expertise = data.get('expertise', '').strip()
        experience = data.get('experience', '').strip()

        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'Name, email and password are required.'}), 400
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long.'}), 400
        if role not in ['farmer', 'consultant']:
            role = 'farmer'

        existing_user = find_user_by_email(email)
        if existing_user:
            return jsonify({'success': False, 'message': 'An account with this email already exists.'}), 409

        hashed_pw = hash_password(password)
        user_id = create_user(name, email, hashed_pw, role=role, phone=phone, location=location, expertise=expertise, experience=experience)
        token = generate_token(user_id)

        return jsonify({
            'success': True,
            'message': f'Welcome aboard, {name}! Registered as {role.capitalize()}.',
            'token': token,
            'user': {'id': user_id, 'name': name, 'email': email, 'role': role}
        }), 201

    except Exception as e:
        print(f"[ERROR] Registration failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500


@app.route('/login', methods=['POST'])
def login():
    """Authenticate a user and return a JWT token (includes role info)."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required.'}), 400

        user = find_user_by_email(email)
        if not user or not verify_password(password, user['password']):
            return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

        user_id = str(user['_id'])
        token = generate_token(user_id)

        return jsonify({
            'success': True,
            'message': f'Welcome back, {user["name"]}!',
            'token': token,
            'user': {
                'id': user_id,
                'name': user['name'],
                'email': user['email'],
                'role': user.get('role', 'farmer'),
                'phone': user.get('phone', ''),
                'location': user.get('location', '')
            }
        }), 200

    except Exception as e:
        print(f"[ERROR] Login failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Login failed. Please try again.'}), 500


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
        return jsonify({'success': False, 'message': 'Failed to retrieve prediction history.'}), 500


# ============================================================
# API Routes - Module 1: Smart Advisor Chatbot
# ============================================================

@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')

@app.route('/api/chat', methods=['POST'])
@token_required
def chat(current_user):
    """Send a message to KrishiBot and get AI response."""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        if not message:
            return jsonify({'success': False, 'message': 'Message is required'}), 400
        result = send_message(current_user['_id'], message, session_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/sessions', methods=['GET'])
@token_required
def chat_sessions(current_user):
    sessions = get_chat_sessions(current_user['_id'])
    return jsonify({'success': True, 'sessions': sessions}), 200

@app.route('/api/chat/history/<session_id>', methods=['GET'])
@token_required
def chat_history(current_user, session_id):
    messages = get_session_messages(current_user['_id'], session_id)
    return jsonify({'success': True, 'messages': messages}), 200


# ============================================================
# API Routes - Module 2: Schemes, Subsidies & Carbon Credits
# ============================================================

@app.route('/schemes')
def schemes_page():
    return render_template('schemes.html')

@app.route('/api/schemes', methods=['GET'])
def api_schemes():
    """Get government schemes with optional category/state filter."""
    category = request.args.get('category')
    state = request.args.get('state', 'Maharashtra')
    schemes = get_schemes(category=category, state=state)
    return jsonify({'success': True, 'schemes': schemes, 'total': len(schemes)}), 200

@app.route('/api/carbon-credits', methods=['GET'])
def api_carbon_credits():
    data = get_carbon_credits()
    return jsonify({'success': True, 'data': data}), 200

@app.route('/api/scheme-categories', methods=['GET'])
def api_scheme_categories():
    return jsonify({'success': True, 'categories': get_scheme_categories()}), 200


# ============================================================
# API Routes - Module 3: Mandi / Market Prices
# ============================================================

@app.route('/prices')
def prices_page():
    return render_template('prices.html')

@app.route('/api/prices', methods=['GET'])
def api_prices():
    """Get mandi prices. Query params: commodity, state"""
    commodity = request.args.get('commodity', 'Grapes')
    state = request.args.get('state', 'Maharashtra')
    result = get_prices(commodity=commodity, state=state)
    return jsonify(result), 200

@app.route('/api/commodities', methods=['GET'])
def api_commodities():
    return jsonify({'success': True, 'commodities': get_all_commodities()}), 200


# ============================================================
# API Routes - Module 4: Disease Recommendations
# ============================================================

@app.route('/recommendations')
def recommendations_page():
    return render_template('recommendations.html')

@app.route('/api/recommend', methods=['GET'])
def api_recommend():
    """Get treatment recommendation for a detected disease."""
    disease = request.args.get('disease', 'Healthy')
    result = get_recommendation(disease)
    return jsonify(result), 200


# ============================================================
# API Routes - Module 5: Community Forum
# ============================================================

@app.route('/forum')
def forum_page():
    return render_template('forum.html')

@app.route('/forum/thread/<thread_id>')
def forum_thread_page(thread_id):
    return render_template('forum_thread.html')

@app.route('/api/forum/threads', methods=['GET'])
def api_get_threads():
    category = request.args.get('category')
    search = request.args.get('search')
    page = int(request.args.get('page', 1))
    return jsonify(get_threads(category=category, search=search, page=page)), 200

@app.route('/api/forum/threads', methods=['POST'])
@token_required
def api_create_thread(current_user):
    data = request.get_json()
    result = create_thread(
        user_id=current_user['_id'],
        user_name=current_user['name'],
        user_role=current_user.get('role', 'farmer'),
        title=data.get('title', '').strip(),
        body=data.get('body', '').strip(),
        category=data.get('category', 'general'),
        tags=data.get('tags', [])
    )
    return jsonify(result), 201 if result['success'] else 400

@app.route('/api/forum/threads/<thread_id>', methods=['GET'])
def api_thread_detail(thread_id):
    return jsonify(get_thread_detail(thread_id)), 200

@app.route('/api/forum/threads/<thread_id>/replies', methods=['POST'])
@token_required
def api_add_reply(current_user, thread_id):
    data = request.get_json()
    result = add_reply(
        thread_id=thread_id,
        user_id=current_user['_id'],
        user_name=current_user['name'],
        user_role=current_user.get('role', 'farmer'),
        body=data.get('body', '').strip(),
        is_solution=data.get('is_solution', False)
    )
    return jsonify(result), 201 if result['success'] else 400

@app.route('/api/forum/threads/<thread_id>/solve/<reply_id>', methods=['POST'])
@token_required
def api_mark_solution(current_user, thread_id, reply_id):
    result = mark_solution(thread_id, reply_id, current_user['_id'])
    return jsonify(result), 200

@app.route('/api/forum/stats', methods=['GET'])
def api_forum_stats():
    return jsonify({'success': True, 'stats': get_forum_stats(), 'categories': FORUM_CATEGORIES}), 200


# ============================================================
# API Routes - Module 6: Equipment Marketplace
# ============================================================

@app.route('/marketplace')
def marketplace_page():
    return render_template('marketplace.html')

@app.route('/api/marketplace/ads', methods=['GET'])
def api_get_ads():
    category = request.args.get('category')
    search = request.args.get('search')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    condition = request.args.get('condition')
    location = request.args.get('location')
    page = int(request.args.get('page', 1))
    return jsonify(get_ads(
        category=category, search=search,
        min_price=min_price, max_price=max_price,
        condition=condition, location=location, page=page
    )), 200

@app.route('/api/marketplace/ads', methods=['POST'])
@token_required
def api_create_ad(current_user):
    """Create a new equipment listing. Supports JSON body."""
    try:
        data = request.get_json()
        result = create_ad(
            user_id=current_user['_id'],
            user_name=current_user['name'],
            user_phone=current_user.get('phone', ''),
            title=data.get('title', '').strip(),
            description=data.get('description', '').strip(),
            price=float(data.get('price', 0)),
            category=data.get('category', 'other'),
            condition=data.get('condition', 'good'),
            location=data.get('location', current_user.get('location', '')),
            negotiable=data.get('negotiable', True),
            image_paths=data.get('image_paths', [])
        )
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/marketplace/ads/<ad_id>', methods=['GET'])
def api_get_ad(ad_id):
    return jsonify(get_ad_detail(ad_id)), 200

@app.route('/api/marketplace/ads/<ad_id>/status', methods=['PUT'])
@token_required
def api_update_ad_status(current_user, ad_id):
    data = request.get_json()
    result = update_ad_status(ad_id, current_user['_id'], data.get('status', 'inactive'))
    return jsonify(result), 200

@app.route('/api/marketplace/ads/<ad_id>', methods=['DELETE'])
@token_required
def api_delete_ad(current_user, ad_id):
    result = delete_ad(ad_id, current_user['_id'])
    return jsonify(result), 200

@app.route('/api/marketplace/my-ads', methods=['GET'])
@token_required
def api_my_ads(current_user):
    ads = get_user_ads(current_user['_id'])
    return jsonify({'success': True, 'ads': ads}), 200

@app.route('/api/marketplace/stats', methods=['GET'])
def api_marketplace_stats():
    return jsonify({'success': True, 'stats': get_marketplace_stats(), 'categories': EQUIPMENT_CATEGORIES}), 200


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
        init_schemes_data()   # Seed schemes & carbon credit data
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
        debug=False         # Disable debug mode to prevent reloader connection resets on Windows
    )
