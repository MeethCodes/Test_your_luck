import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv 

# Import the configuration settings
from . import config 

# MongoDB setup and utility functions
from .services import db_service # Relative import

# User-related routes (modularized via blueprint)
from .routes.user_routes import user_bp # Relative import
# Game-related routes
from .routes.game_routes import game_bp # Relative import


# --- 1. Load Config and Init Database ---

# Load environment variables (from .env)
load_dotenv() 

# --- 2. Create and Configure Flask App (Directly) ---

# NEW FIX: Remove the create_app() function and define the 'app' object directly.
app = Flask(
    __name__, 
    static_folder="../frontend", 
    static_url_path="/"
)

# Pull in settings from config.py
app.config.from_object(config)

# Allow frontend to talk to backend (CORS setup)
CORS(app)

# Connect to MongoDB and set up TTL index for cleanup
db_service.init_db()

# --- 3. Register Blueprints ---

app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(game_bp, url_prefix='/api/game')


# --- 4. Define Routes ---

@app.route("/api/status", methods=["GET"])
def get_status():
    """Quick ping to verify API is up."""
    return jsonify({"status": "API is online! 🚀"})

@app.route("/")
def serve_frontend():
    """Delivers the main frontend HTML file."""
    return send_from_directory(app.static_folder, "index.html")

# --- 5. Run the App Locally (No change to this block) ---
if __name__ == "__main__":
    app.run(debug=True, port=5000)