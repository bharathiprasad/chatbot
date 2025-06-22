from flask import Flask, render_template, request, jsonify, session
import uuid
import os
from datetime import datetime
import re
import random
from typing import Dict, List, Tuple, Optional

# Import our chatbot classes (assuming they're in the same file or imported)
class SimpleChatBot:
    """A simple rule-based chatbot with pattern matching and responses."""
    
    def __init__(self):
        self.name = "ChatBot"
        self.patterns = {
            r'hello|hi|hey|greetings': [
                "Hello! How can I help you today?",
                "Hi there! What's on your mind?",
                "Hey! Nice to meet you!",
                "Greetings! How are you doing?"
            ],
            r'how are you|how do you do': [
                "I'm doing great, thank you for asking!",
                "I'm fantastic! How about you?",
                "All good here! Thanks for checking in."
            ],
            r'what.*your name|who are you': [
                f"I'm {self.name}, your friendly chatbot assistant!",
                f"My name is {self.name}. I'm here to help you!",
                f"I go by {self.name}. What should I call you?"
            ],
            r'bye|goodbye|see you|farewell': [
                "Goodbye! Have a wonderful day!",
                "See you later! Take care!",
                "Farewell! It was nice chatting with you!",
                "Bye! Come back anytime!"
            ],
            r'thank you|thanks': [
                "You're welcome!",
                "Happy to help!",
                "My pleasure!",
                "Anytime!"
            ],
            r'time|what time': [
                f"The current time is {datetime.now().strftime('%H:%M:%S')}",
                f"It's {datetime.now().strftime('%I:%M %p')} right now."
            ],
            r'date|today': [
                f"Today is {datetime.now().strftime('%B %d, %Y')}",
                f"The date today is {datetime.now().strftime('%Y-%m-%d')}"
            ],
            r'help|what can you do': [
                "I can chat with you, answer simple questions, tell you the time and date, and have a friendly conversation!",
                "I'm here to chat! Ask me about the time, date, or just talk with me!",
                "I can help with basic conversation, tell time, and answer simple questions. What would you like to talk about?"
            ],
            r'joke|funny|humor': [
                "Why don't scientists trust atoms? Because they make up everything!",
                "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                "Why don't programmers like nature? It has too many bugs!",
                "I'm reading a book about anti-gravity. It's impossible to put down!"
            ]
        }
        
        self.fallback_responses = [
            "That's interesting! Tell me more.",
            "I'm not sure I understand. Could you rephrase that?",
            "Hmm, I don't have a good response for that. What else would you like to talk about?",
            "I'm still learning! Can you ask me something else?",
            "That's beyond my current knowledge. What else can I help you with?"
        ]
        
        self.conversation_history = []
        self.user_preferences = {}
        self.context = {}
    
    def preprocess_input(self, user_input: str) -> str:
        """Clean and normalize user input."""
        return user_input.lower().strip()
    
    def find_match(self, user_input: str) -> Optional[str]:
        """Find matching pattern and return a random response."""
        processed_input = self.preprocess_input(user_input)
        
        for pattern, responses in self.patterns.items():
            if re.search(pattern, processed_input):
                return random.choice(responses)
        
        return None
    
    def _handle_name_introduction(self, user_input: str) -> str:
        """Handle user name introduction."""
        processed_input = self.preprocess_input(user_input)
        match = re.search(r'my name is (\w+)|i am (\w+)|call me (\w+)', processed_input)
        
        if match:
            name = next(group for group in match.groups() if group is not None)
            self.user_preferences['name'] = name.title()
            self.context['user_name'] = name.title()
            return f"Nice to meet you, {name.title()}! I'll remember your name."
        
        return "Nice to meet you!"
    
    def get_response(self, user_input: str) -> str:
        """Generate response for user input."""
        # Store conversation
        self.conversation_history.append(("user", user_input))
        
        # Handle name introduction
        processed_input = self.preprocess_input(user_input)
        if re.search(r'my name is (\w+)|i am (\w+)|call me (\w+)', processed_input):
            response = self._handle_name_introduction(user_input)
        else:
            # Find matching response
            response = self.find_match(user_input)
            
            if response is None:
                # Personalized fallback if we know the user's name
                if 'user_name' in self.context:
                    personalized_fallbacks = [
                        f"That's interesting, {self.context['user_name']}! Tell me more.",
                        f"I'm not sure about that, {self.context['user_name']}. Could you explain?",
                        f"Hmm, {self.context['user_name']}, that's something new to me!"
                    ]
                    response = random.choice(personalized_fallbacks)
                else:
                    response = random.choice(self.fallback_responses)
        
        # Store bot response
        self.conversation_history.append(("bot", response))
        
        return response
    
    def get_conversation_history(self) -> List[Tuple[str, str]]:
        """Return the conversation history."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()


# Flask Application
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Store chatbot sessions
chatbot_sessions = {}

def get_or_create_session_id():
    """Get existing session ID or create a new one."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def get_chatbot_session(session_id: str) -> SimpleChatBot:
    """Get or create a chatbot session."""
    if session_id not in chatbot_sessions:
        chatbot_sessions[session_id] = SimpleChatBot()
    return chatbot_sessions[session_id]

@app.route('/')
def index():
    """Main chat interface."""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """API endpoint for chat messages."""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Get or create session
        session_id = get_or_create_session_id()
        chatbot = get_chatbot_session(session_id)
        
        # Get bot response
        bot_response = chatbot.get_response(user_message)
        
        # Return response
        return jsonify({
            'response': bot_response,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    """Get conversation history for current session."""
    try:
        session_id = get_or_create_session_id()
        chatbot = get_chatbot_session(session_id)
        
        history = []
        for speaker, message in chatbot.get_conversation_history():
            history.append({
                'speaker': speaker,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({'history': history})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history for current session."""
    try:
        session_id = get_or_create_session_id()
        chatbot = get_chatbot_session(session_id)
        chatbot.clear_history()
        
        return jsonify({'message': 'History cleared successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get chatbot statistics."""
    try:
        session_id = get_or_create_session_id()
        chatbot = get_chatbot_session(session_id)
        
        history = chatbot.get_conversation_history()
        user_messages = [msg for speaker, msg in history if speaker == 'user']
        bot_messages = [msg for speaker, msg in history if speaker == 'bot']
        
        stats = {
            'total_messages': len(history),
            'user_messages': len(user_messages),
            'bot_messages': len(bot_messages),
            'session_id': session_id,
            'user_name': chatbot.context.get('user_name', 'Unknown'),
            'active_sessions': len(chatbot_sessions)
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    print("Starting Flask ChatBot Server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)