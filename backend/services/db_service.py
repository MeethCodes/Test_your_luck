import pymongo
import datetime
import sys

# Import the configuration settings
import config

# Global variables to hold the connected objects
client = None
db = None
user_collection = None
game_collection = None

# --- Helper Function to Set Up TTL Index ---
def _create_ttl_index():
    """
    Creates a partial Time-To-Live (TTL) index on the Users collection.
    This ensures guest documents are automatically deleted after inactivity.
    """
    global user_collection
    
    try:
        # Index on 'last_activity', expires after the configured seconds (e.g., 3600)
        # ONLY applies where is_guest is True.
        user_collection.create_index(
            [("last_activity", pymongo.ASCENDING)],
            expireAfterSeconds=config.GUEST_TTL_SECONDS,
            partialFilterExpression={"is_guest": True}
        )
        print("Database Setup: TTL Index on 'Users' collection created successfully. (Guest auto-deletion enabled)")
    except Exception as e:
        # This handles cases where the index might already exist or a configuration error occurred.
        print(f"Warning: Could not create TTL index. Error: {e}")

# --- Main Database Initialization Function ---
def init_db():
    """
    Initializes the MongoDB connection and global collection references.
    This function should be called once when the backend application starts.
    """
    global client, db, user_collection, game_collection
    
    # 1. Establish Connection
    try:
        # Use MongoClient and the URI from the config file
        client = pymongo.MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # Check connection status
        client.admin.command('ismaster')
        
        print(f"Connection with MongoDB successful! ✅")
        
    except pymongo.errors.ConnectionFailure as e:
        print(f"Connection attempt failed! ❌ Error: {e}")
        # Use sys.exit(1) to stop the program if the critical database connection fails
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during connection: {e}")
        sys.exit(1)
        
    # 2. Access Database and Collections
    db = client[config.DB_NAME]
    user_collection = db.Users
    game_collection = db.Game_History
    
    # 3. Perform Initial Setup (Create Indexes)
    _create_ttl_index()

# --- CORE CRUD FUNCTIONS ---


def find_user_by_username(username):
    """
    Retrieves a single user document based on the username.
    
    Returns:
        dict or None: The user document if found, otherwise None.
    """
    global user_collection
    
    # Use find_one() for efficient retrieval of a single document
    user_data = user_collection.find_one({"username": username})
    
    return user_data

# --- NEW FUNCTION FOR CREATE OPERATION ---
def insert_user(username, password_hash, is_guest):
    """
    Creates a new user or guest document in the Users collection.
    
    Args:
        username (str): The unique username.
        password_hash (str or None): Hashed password for users, None for guests.
        is_guest (bool): Flag to determine account type.
        
    Returns:
        ObjectId: The _id of the newly created document.
    """
    global user_collection
    
    # 1. Build the base document
    user_document = {
        "username": username,
        "is_guest": is_guest,
        "created_at": datetime.datetime.utcnow() 
    }
    
    # 2. Add fields specific to guests or signed-up users
    if is_guest:
        # Crucial for the TTL index: add the last_activity timestamp for guests
        user_document["last_activity"] = datetime.datetime.utcnow()
    else:
        # For signed-up users, store the hashed password
        user_document["password_hash"] = password_hash
        
    # 3. Perform the Create operation (C in CRUD)
    result = user_collection.insert_one(user_document)
    
    # Return the unique MongoDB ID (required by the user_routes.py logic)
    return result.inserted_id