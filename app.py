from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from transformers import pipeline

app = Flask(__name__)
CORS(app)

summarizer = pipeline("summarization")

API_ENDPOINT = "https://newsapi.org/v2/top-headlines"
API_KEY = "9f5e7057d622425db2b24106840aeb5a"

# In-memory storage for user preferences (use a database in production)
users = {}


@app.route('/register', methods=['POST'])
def register_user():
    user_id = request.json.get('userId')
    interest = request.json.get('interest')

    if not user_id or not interest:
        return jsonify({"error": "User ID and interest are required!"}), 400

    users[user_id] = interest
    return jsonify({"message": "Registered successfully!"})


@app.route('/get-news', methods=['POST'])
def get_news():
    user_id = request.json.get('userId')
    if not user_id or user_id not in users:
        return jsonify({"error": "Invalid User ID!"}), 400

    interest = users[user_id]
    articles = fetch_articles(interest)
    summarized_articles = summarize_articles(articles)

    return jsonify(summarized_articles)


# ... [rest of the functions remain unchanged]

if __name__ == "__main__":
    app.run(debug=True)
