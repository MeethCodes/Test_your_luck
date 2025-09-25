// --- 1. GLOBAL STATE AND HELPERS ---

// Store user data retrieved from the backend after login/signup/guest play
let CURRENT_USER_ID = null;
let CURRENT_USERNAME = null;
let API_BASE_URL = "http://127.0.0.1:5000/api"; // Base URL for all API calls

// Store the secret number locally only after the game starts (for debugging/internal use)
// NOTE: For security, the user doesn't strictly need this, but we'll use it to visualize state.
let GAME_SECRET_NUMBER = null; 

// References to DOM elements
const $ = selector => document.querySelector(selector);

// Function to control screen visibility
const showScreen = (screenId) => {
    // Hide all main screens
    $('.main-screen').forEach(screen => screen.classList.add('hidden'));
    // Show the requested screen
    $(`#${screenId}`).classList.remove('hidden');
};

// --- 2. NAVIGATION AND AUTHENTICATION LOGIC ---

// Handles communication with the backend for login/signup/guest
async function handleAuth(endpoint, username = null, password = null) {
    const messageEl = $('#auth-message');
    messageEl.textContent = 'Processing...';

    const body = {};
    if (username) body.username = username;
    if (password) body.password = password;

    try {
        const response = await fetch(`${API_BASE_URL}/user/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (response.ok) {
            // Success: Store user ID and name, then move to setup
            CURRENT_USER_ID = data.user_id;
            CURRENT_USERNAME = data.username || username; 
            
            // Update greeting on setup screen
            $('.user-greeting').textContent = `Hello, ${CURRENT_USERNAME}!`;
            showScreen('setup-container');
        } else {
            // Failure: Display error from backend
            messageEl.textContent = data.message || `Error: Status ${response.status}`;
        }
    } catch (error) {
        console.error('Fetch error:', error);
        messageEl.textContent = 'Network error. Could not connect to the server.';
    }
}

// --- Event Handlers for Authentication Screen ---

// 1. Login Handler
$('#login-btn').addEventListener('click', () => {
    const username = $('#login-username').value;
    const password = $('#login-password').value;
    handleAuth('login', username, password);
});

// 2. Register Handler
$('#signup-btn').addEventListener('click', () => {
    const username = $('#login-username').value;
    const password = $('#login-password').value;
    handleAuth('signup', username, password);
});

// 3. Guest Play Handler
$('#guest-btn').addEventListener('click', () => {
    handleAuth('guest'); // No username/password needed for guest
});

// 4. Logout Handler (Returns user to login screen)
$('#logout-btn').addEventListener('click', () => {
    CURRENT_USER_ID = null;
    CURRENT_USERNAME = null;
    showScreen('login-container');
    // NOTE: In a production app, you might also call a backend '/logout' route here
});


// --- 3. GAME SETUP LOGIC ---

const maxLimitInput = $('#max-limit');
const startGameBtn = $('#start-game-btn');

// Input Listener: Enables the start button if range is valid (10-100)
maxLimitInput.addEventListener('input', () => {
    const max = parseInt(maxLimitInput.value);
    
    // Validate against constraints defined in the backend
    if (max >= 10 && max <= 100) {
        startGameBtn.disabled = false;
        $('#setup-message').textContent = '';
    } else {
        startGameBtn.disabled = true;
        $('#setup-message').textContent = 'Please enter a number between 10 and 100.';
    }
});

// Start Game Handler: Calls the /api/game/start endpoint
startGameBtn.addEventListener('click', async () => {
    const max = parseInt(maxLimitInput.value);
    const messageEl = $('#setup-message');
    
    // Final check for user ID and range
    if (!CURRENT_USER_ID || max < 10 || max > 100) {
        messageEl.textContent = 'Setup error. Please log in again or check your range.';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/game/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: CURRENT_USER_ID, max: max })
        });

        const data = await response.json();

        if (response.ok) {
            // Success: Game started, move to the game container
            // Update the display with the new range
            $('#game-min').textContent = '1';
            $('#game-max').textContent = max;
            $('#attempts-counter').textContent = 'Attempts: 0';
            $('#game-feedback').textContent = data.message;
            $('#user-guess').value = '';
            $('#check-btn').disabled = false;
            
            showScreen('game-container');
        } else {
            messageEl.textContent = data.message || 'Failed to start game.';
        }
    } catch (error) {
        messageEl.textContent = 'Network error starting game.';
    }
});


// --- 4. GAME PLAY LOGIC (To be completed in the next step) ---

const userGuessInput = $('#user-guess');
const checkBtn = $('#check-btn');

// Enables the check button when a guess is entered
userGuessInput.addEventListener('input', () => {
    checkBtn.disabled = userGuessInput.value.length === 0;
});


// Handler for the CHECK button (This completes the loop!)
checkBtn.addEventListener('click', async () => {
    const guess = parseInt(userGuessInput.value);
    const feedbackEl = $('#game-feedback');
    const attemptsEl = $('#attempts-counter');

    if (isNaN(guess)) {
        feedbackEl.textContent = 'Please enter a valid number.';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/game/guess`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: CURRENT_USER_ID, guess: guess })
        });
        
        const data = await response.json();

        if (response.ok) {
            feedbackEl.textContent = data.message;
            attemptsEl.textContent = `Attempts: ${data.attempts}`;

            if (data.status === 'won') {
                feedbackEl.style.color = '#27ae60'; // Green for success
                checkBtn.disabled = true;
                $('#user-guess').disabled = true;
                $('#restart-btn').classList.remove('hidden');
            } else {
                feedbackEl.style.color = '#f39c12'; // Orange for feedback
            }

        } else {
            feedbackEl.textContent = data.message || 'Game error.';
            feedbackEl.style.color = '#e74c3c';
        }
    } catch (error) {
        feedbackEl.textContent = 'Network error during guess.';
        feedbackEl.style.color = '#e74c3c';
    }
});


// Restart Button Handler
$('#restart-btn').addEventListener('click', () => {
    $('#restart-btn').classList.add('hidden');
    $('#user-guess').disabled = false;
    // Go back to the setup screen to choose a new range
    showScreen('setup-container'); 
});


// --- 5. INITIALIZATION ---

// Ensure the first screen shown is the login container when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Collect all main screen elements (since querySelectorAll is not available in all environments)
    // We use a simpler, common method for demonstration
    const screens = document.querySelectorAll('.main-screen');
    if (screens.length > 0) {
        screens.forEach(screen => {
            if (screen.id !== 'login-container') {
                screen.classList.add('hidden');
            }
        });
    }

    // Since we used a simple querySelectorAll mock above, ensure the login screen is visible
    showScreen('login-container'); 
});

// Mock for querySelectorAll to allow simple iteration (since standard QS is an object)
const qsa = (selector) => Array.from(document.querySelectorAll(selector));
$('.main-screen').forEach = qsa('.main-screen').forEach;