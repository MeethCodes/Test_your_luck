# backend/routes/game_routes.py

from flask import Blueprint, request, jsonify, session
import random
from services import db_service 

# Create a Blueprint instance for game-related routes
game_bp = Blueprint('game_bp', __name__)

# --- SERVER-SIDE GAME STATE (Temporary in-memory storage) ---
# This dictionary will hold the secret number and attempts for each active user.
# The key will be the user's ID.
active_games = {}

@game_bp.route('/start', methods=['POST'])
def start_game():
    """Handles starting a new game session with a fixed min range of 1."""
    data = request.get_json()
    
    # The minimum range is now FIXED at 1
    min_range = 1 
    
    # The user only sends the desired max_range
    max_range = data.get('max') 
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"message": "Authentication required to start a game."}), 401

    # 1. Input Validation: Check that the max range is a number and is within rules (10-100)
    # The 'min_range' check is simplified since it's always 1.
    if not isinstance(max_range, int) or max_range < 10 or max_range > 100:
        return jsonify({
            "message": "Invalid range. Max range must be a whole number between 10 and 100."
        }), 400

    # 2. Game Logic: Generate secret number
    secret_number = random.randint(min_range, max_range)

    # 3. State Management: Store the game state
    active_games[user_id] = {
        'secret_number': secret_number,
        'attempts': 0,
        'min_range': min_range, # Stored as 1
        'max_range': max_range
    }

    # 4. Response
    return jsonify({
        "message": f"New game started. Guess a number between 1 and {max_range}.",
        "range": f"1-{max_range}"
    }), 200

@game_bp.route('/guess', methods=['POST']) 
def handle_guess():
    """Handles a player's guess, compares it to the secret number, and updates the score."""
    data = request.get_json()
    user_id = data.get('user_id')
    guess = data.get('guess')

    # 1. Basic Validation
    if not user_id or guess is None:
        return jsonify({"message": "User ID and guess are required."}), 400

    # 2. Check Active Game State (MUST EXIST)
    if user_id not in active_games:
        return jsonify({"message": "No active game found. Please start a new game."}), 404

    # 3. Retrieve Game State and Update Attempts (U in CRUD logic for state)
    game_state = active_games[user_id]
    game_state['attempts'] += 1
    
    secret = game_state['secret_number']
    
    # 4. Compare Guess
    if guess == secret:
        # WIN CONDITION: Game is over
        score = game_state['attempts']
        
        # --- NEW CODE: Save the score to MongoDB ---
        try:
            db_service.save_game_history(
                user_id, 
                score, 
                game_state['min_range'], 
                game_state['max_range'], 
                game_state['secret_number']
            )
            message = f"Correct! Score saved successfully in {score} attempts."
        except Exception as e:
            # Handle potential database error, but still clear the game state
            print(f"Error saving game history for user {user_id}: {e}")
            message = f"Correct! You won in {score} attempts, but score could not be saved."


        del active_games[user_id] # Clear state
        
        return jsonify({
            "message": message,
            "status": "won",
            "attempts": score
        }), 200
        
    elif guess < secret:
        result = "try higher"
    else: # guess > secret
        result = "try lower"
        
    # 5. Response for ongoing game
    return jsonify({
        "message": result,
        "attempts": game_state['attempts'],
        "status": "in_progress"
    }), 200

# backend/routes/game_routes.py (Add this new route)

@game_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard_route():
    """Retrieves and returns the top 10 scores using the Aggregation Pipeline."""
    
    try:
        # Call the new function from db_service
        leaderboard = db_service.get_leaderboard(limit=10)
        
        return jsonify(leaderboard), 200
        
    except Exception as e:
        print(f"Error retrieving leaderboard: {e}")
        return jsonify({"message": "Failed to retrieve leaderboard data."}), 500