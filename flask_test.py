from flask import Flask, render_template, request

# Initialize Flask app
app = Flask(__name__)

# 1. Basic Routes (GET only)
@app.route('/')
def home():
    """Homepage - Returns a simple text response"""
    return "Hello, Flask!"

@app.route('/about')
def about():
    """About Page - Simple text explaining the app"""
    return "This is a Flask-powered NLP app."

# 2. Rendering HTML Pages
@app.route('/welcome')
def welcome():
    """Render a welcome HTML page"""
    return render_template("welcome.html")

@app.route('/welcome_pretty')
def welcome_pretty():
    """Render a styled (pretty) welcome page"""
    return render_template("welcome_pretty.html")

# 3. Handling GET and POST Requests
@app.route('/process', methods=['GET', 'POST'])
def process():
    """Handles both GET and POST requests to process user input"""
    text = None

    if request.method == 'POST':
        text = request.form.get("user_input")  # Safer way to access form data
    else:
        text = request.args.get("user_input")  # Extract query parameter from URL
    
    # Handle case where no input is provided
    if not text:
        return "Please enter some text."

    return f"You entered: {text}"

# 4. Teaching GET vs. POST with Different Routes
@app.route('/welcome_post', methods=['POST'])
def welcome_post():
    """Demonstrates POST-only route (Expecting form data)"""
    text = request.form.get("user_input", "No data provided")
    return f"Welcome (POST): {text}"

@app.route('/welcome_get', methods=['GET'])
def welcome_get():
    """Demonstrates GET-only route (Expecting URL parameters)"""
    text = request.args.get("user_input", "No data provided")
    return f"Welcome (GET): {text}"

# 5. Dynamic Routes (Extracting Data from URL)
@app.route('/user/<username>') 
def show_user(username): 
    """Greet the user based on the URL parameter"""
    return f'Hello, {username}!'

# 6. Running the Flask App
if __name__ == "__main__":
    app.run(debug=True)
