from flask import Flask, render_template, request
import random

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

@app.route('/nlp-apps')
def nlp_apps():
    """About Page - Simple text explaining the app"""
    return "NLP apps are so cool."

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
    else: # if the method is GET
        text = request.args.get("user_input")  # Extract query parameter from URL
    
    # Handle case where no input is provided
    if not text:
        return "Please enter some text."

    return f"You entered: {text}"

# 4. Teaching GET vs. POST with Different Routes
@app.route('/welcome_post')
def welcome_post():
    """Demonstrates POST-only route (Expecting form data)"""
    return render_template("welcome_post.html")

@app.route('/welcome_get')
def welcome_get():
    """Demonstrates GET-only route (Expecting URL parameters)"""
    return render_template("welcome_get.html")

# 5. Dynamic Routes (Extracting Data from URL)
@app.route('/user/<username>') 
def show_user(username): 
    """Greet the user based on the URL parameter"""
    return f'Hello, {username}!'

with open("templates/random_generator.html", "r") as file:
    html_template = file.read()
    
# 6. Random order generator of unordered list
@app.route("/shuffle", methods=["GET"])
def shuffle_names():
    shuffled_names_html = ""

    names = request.args.get("names", "")
    
    if names != "":
        name_list = [name.strip() for name in names.split(",") if name.strip()]
        random.shuffle(name_list)
        shuffled_names_html = "<h2>🔀 Shuffled Order 🔀</h2><ul>"
        shuffled_names_html += "".join(f"<li>{name}</li>" for name in name_list)
        shuffled_names_html += "</ul>"
    
    print(shuffled_names_html)
    
    return html_template.replace("{{ shuffled_names }}", shuffled_names_html)

# Running the Flask App
if __name__ == "__main__":
    app.run(debug=True)