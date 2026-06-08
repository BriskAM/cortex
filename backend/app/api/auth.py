from flask import Blueprint, request, jsonify, current_app
from flask_security import hash_password, auth_token_required, current_user
from flask_security.utils import verify_and_update_password, login_user, logout_user
from backend.app.extensions import db
import os
import requests
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

@auth_bp.route('/settings', methods=['POST'])
@auth_token_required
def update_settings():
    """Update user settings like GitHub OAuth token."""
    data = request.get_json() or {}
    github_token = data.get('github_token')
    
    # Allow clearing the token by passing empty string/None
    if 'github_token' in data:
        if github_token:
            current_user.github_token = github_token.strip()
        else:
            current_user._github_token = None
            
    try:
        db.session.commit()
        return jsonify({
            "message": "Settings updated successfully",
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "active": current_user.active,
                "has_github_token": bool(current_user._github_token)
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to save settings: {str(e)}"}), 500

@auth_bp.route('/github/login', methods=['GET'])
def github_login():
    """Return the GitHub authorize URL."""
    client_id = os.getenv("GITHUB_CLIENT_ID")
    if not client_id:
        return jsonify({"error": "GitHub OAuth is not configured on this server"}), 501
    url = f"https://github.com/login/oauth/authorize?client_id={client_id}&scope=read:user,read:repo"
    return jsonify({"url": url}), 200

@auth_bp.route('/github/callback', methods=['POST'])
def github_callback():
    """Handle GitHub OAuth authorization code redirect exchange."""
    data = request.get_json() or {}
    code = data.get('code')
    if not code:
        return jsonify({"error": "OAuth code parameter is required"}), 400
        
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return jsonify({"error": "GitHub OAuth configuration is incomplete on this server"}), 501
        
    # 1. Exchange OAuth code for an access token
    try:
        resp = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code
            },
            timeout=10
        )
        resp_data = resp.json()
        access_token = resp_data.get("access_token")
        if not access_token:
            return jsonify({"error": f"Token exchange failed: {resp_data.get('error_description', 'Unknown error')}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to connect to GitHub OAuth endpoint: {str(e)}"}), 500
        
    # 2. Query GitHub User details
    try:
        user_resp = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/json"
            },
            timeout=10
        )
        gh_user = user_resp.json()
        email = gh_user.get("email")
        
        # If email is private, query emails list
        if not email:
            emails_resp = requests.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json"
                },
                timeout=10
            )
            emails = emails_resp.json()
            for em in emails:
                if em.get("primary") and em.get("verified"):
                    email = em.get("email")
                    break
            if not email and emails:
                email = emails[0].get("email")
                
        if not email:
            # Fallback construct
            email = f"{gh_user.get('login')}@users.noreply.github.com"
    except Exception as e:
        return jsonify({"error": f"Failed to query GitHub user profile details: {str(e)}"}), 500
        
    # 3. Resolve user in local database
    user_datastore = current_app.extensions['security'].datastore
    user = user_datastore.find_user(email=email)
    
    try:
        if not user:
            # Register new user dynamically
            user = user_datastore.create_user(
                email=email,
                password=hash_password(uuid.uuid4().hex),
                active=True,
                fs_uniquifier=uuid.uuid4().hex
            )
            
        # Set/update the encrypted github token
        user.github_token = access_token
        db.session.commit()
        
        # Login and return access token
        login_user(user)
        token = user.get_auth_token()
        db.session.commit()
        
        return jsonify({
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "active": user.active,
                "has_github_token": True
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"GitHub authentication integration failed: {str(e)}"}), 500
