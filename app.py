from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
from aeris_assistant import get_aeris_response
import os
import json
import datetime
import traceback

app = Flask(__name__)

# === Mail Configuration ===
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your.email@gmail.com'  # Replace with sender email
app.config['MAIL_PASSWORD'] = 'your_app_password'     # Use App Password, NOT regular Gmail password
app.config['MAIL_DEFAULT_SENDER'] = 'your.email@gmail.com'

mail = Mail(app)

# === Feedback Mail Route ===
@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.form
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    try:
        msg = Message(f"New Feedback from {name}",
                      recipients=["bogadiyasasbogadiyasasri@gmail.com"])
        msg.body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        mail.send(msg)
        return jsonify({"success": True})
    except Exception as e:
        print("Mail error:", e)
        return jsonify({"success": False}), 500

# === Aeris Assistant Logic ===

PROMPTS_FILE = os.path.join("logs", "aeris_log.json")

def save_conversation_to_file(user_text, aeris_response):
    conversations = []
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            try:
                conversations = json.load(f)
            except json.JSONDecodeError:
                conversations = []
    conversations.append({
        "user": user_text,
        "aeris": aeris_response,
        "timestamp": datetime.datetime.now().isoformat()
    })
    with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=4)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/query", methods=["POST"])
def query():
    try:
        data = request.get_json()
        user_text = data.get("text", "").strip()
        if not user_text:
            return jsonify({"response": "Please say something."})
        response = get_aeris_response(user_text)
        save_conversation_to_file(user_text, response)
        return jsonify({"response": response})
    
    except Exception as e:
        print("Error:", e)
        print(traceback.format_exc())  # ✅ this shows the full line-by-line traceback
        return jsonify({"response": "Something went wrong. Please try again."})

if __name__ == "__main__":
    app.run(debug=True)
