from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    return jsonify({
        "message": "User registered successfully",
        "user": {"email": email, "id": 1}
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login and return JWT token."""
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    return jsonify({
        "token": "mock-jwt-token-for-dev",
        "user": {
            "id": 1,
            "email": email,
            "active": True
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout current user."""
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/me', methods=['GET'])
def me():
    """Get currently logged in user profile."""
    # Stub response
    return jsonify({
        "user": {
            "id": 1,
            "email": "dev@cortex.dev",
            "active": True
        }
    }), 200
