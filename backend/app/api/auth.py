from flask import Blueprint, request, jsonify, current_app
from flask_security import hash_password, auth_token_required, current_user
from flask_security.utils import verify_and_update_password, login_user, logout_user
from backend.app.extensions import db
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user in the database."""
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    github_token = data.get('github_token')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    user_datastore = current_app.extensions['security'].datastore
    
    # Check if user already exists
    if user_datastore.find_user(email=email):
        return jsonify({"error": "User with this email already registered"}), 409
        
    try:
        # Create user inside datastore
        user = user_datastore.create_user(
            email=email,
            password=hash_password(password),
            active=True,
            fs_uniquifier=uuid.uuid4().hex
        )
        if github_token:
            user.github_token = github_token
            
        db.session.commit()
        return jsonify({
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "email": user.email
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Verify credentials and return access token."""
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    user_datastore = current_app.extensions['security'].datastore
    user = user_datastore.find_user(email=email)
    
    if not user or not verify_and_update_password(password, user):
        return jsonify({"error": "Invalid email or password"}), 401
        
    # Mark user as logged in for the session context
    login_user(user)
    token = user.get_auth_token()
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database commit failed: {str(e)}"}), 500
        
    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "active": user.active
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@auth_token_required
def logout():
    """Logout current user and invalidate token session context."""
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/me', methods=['GET'])
@auth_token_required
def me():
    """Retrieve profile of currently authenticated user."""
    return jsonify({
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "active": current_user.active,
            "has_github_token": bool(current_user._github_token)
        }
    }), 200
