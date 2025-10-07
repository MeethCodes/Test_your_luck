import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv 
# Import the configuration settings
from . import config
# MongoDB setup and utility functions
from .services import db_service
from .routes.user_routes import user_bp
from .routes.game_routes import game_bp


# --- App Factory ---
def create_app():
    
    # NEW FIX: Explicitly set the static URL path to '/' and point to the frontend folder.
    # This tells Flask to serve resources inside '../frontend' directly from the root URL.
    app = Flask(
        __name__, 
        static_folder="../frontend", 
        static_url_path="/"
    )

    # Load environment variables (from .env)
    load_dotenv() 
    
    # Pull in settings from config.py
    app.config.from_object(config)

    # Allow frontend to talk to backend (CORS setup)
    CORS(app)

    # Connect to MongoDB and set up TTL index for cleanup
    db_service.init_db()

    # --- Register Blueprints ---
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(game_bp, url_prefix='/api/game')


    # --- Health Check Route ---
    @app.route("/api/status", methods=["GET"])
    def get_status():
        """Quick ping to verify API is up."""
        return jsonify({"status": "API is online! 🚀"})

    # --- Serve Frontend ---
    @app.route("/")
    def serve_frontend():
        """Delivers the main frontend HTML file."""
        return send_from_directory(app.static_folder, "index.html")

    return app

# Run the app locally (dev mode)
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)