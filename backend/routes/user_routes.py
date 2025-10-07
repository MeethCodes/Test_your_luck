from flask import Blueprint, request, jsonify
from ..services import db_service
import bcrypt
import random
import string

# Blueprint for user-related routes
user_bp = Blueprint('user_bp', __name__)

# Internal helper to generate a random guest username
def _generate_guest_username():
    """Creates a randomized guest username with 8 alphanumeric characters."""
    letters = string.ascii_letters + string.digits
    return 'Guest_' + ''.join(random.choice(letters) for i in range(8))


@user_bp.route('/signup', methods=['POST'])
def signup():
    """Registers a new user with hashed password."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    # Check if username already exists
    if db_service.find_user_by_username(username):
        return jsonify({"message": "Username already taken"}), 409

    # Hash the password and store the user
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        user_id = db_service.insert_user(
            username=username, 
            password_hash=password_hash.decode('utf-8'), 
            is_guest=False
        )
        return jsonify({
            "message": "User created successfully", 
            "user_id": str(user_id)
        }), 201
    except Exception as e:
        print(f"Error during sign up: {e}")
        return jsonify({"message": "Internal server error"}), 500


@user_bp.route('/guest', methods=['POST'])
def guest_play():
    """Creates a guest user session with a generated username."""
    guest_username = _generate_guest_username()
    
    try:
        user_id = db_service.insert_user(
            username=guest_username,
            password_hash=None, 
            is_guest=True
        )
        return jsonify({
            "message": "Guest session started", 
            "user_id": str(user_id), 
            "username": guest_username
        }), 201
    except Exception as e:
        print(f"Error starting guest session: {e}")
        return jsonify({"message": "Internal server error"}), 500


@user_bp.route('/login', methods=['POST'])
def login():
    """Authenticates a registered user using bcrypt password check."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    # Look up user by username
    user = db_service.find_user_by_username(username)

    if user:
        # Block login for guest accounts
        if user.get('is_guest'):
            return jsonify({"message": "Guest accounts cannot log in this way. Please use the 'Play as Guest' button."}), 403
            
        # Validate password
        stored_hash = user.get('password_hash').encode('utf-8')
        
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return jsonify({
                "message": "Login successful",
                "user_id": str(user.get('_id')),
                "username": user.get('username')
            }), 200
        else:
            return jsonify({"message": "Invalid username or password"}), 401
    else:
        return jsonify({"message": "Invalid username or password"}), 401
