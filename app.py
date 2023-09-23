from flask import Flask, jsonify
from flask_cors import CORS
import requests
from transformers import pipeline

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize the summarizer
summarizer = pipeline("summarization")

# Constants
API_ENDPOINT = "https://newsapi.org/v2/everything"
API_KEY = "9f5e7057d622425db2b24106840aeb5a"  # Replace with your actual NewsAPI key
HARDCODED_KEYWORDS = ["technology", "science", "health"]  # You can change or add more keywords

@app.route('/get-news-summaries', methods=['GET'])
def get_news_summaries():
    articles = fetch_articles(HARDCODED_KEYWORDS)
    summarized_articles = summarize_articles(articles)

    return jsonify(summarized_articles)

def fetch_articles(keywords):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    all_articles = []

    for keyword in keywords:
        params = {
            "q": keyword,
            "language": "en",
            "pageSize": 5  # Fetching 5 articles per keyword; adjust as needed
        }

        response = requests.get(API_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()

        all_articles.extend(response.json().get('articles', []))

    return all_articles

def summarize_articles(articles):
    summarized_articles = []

    for article in articles:
        title = article.get("title")
        content = article.get("content", "")
        url = article.get("url")

        if not content:
            continue

        summary = summarizer(content, max_length=100, min_length=30, do_sample=False)[0]['summary_text']

        summarized_articles.append({
            "title": title,
            "summary": summary,
            "url": url
        })

    return summarized_articles

if __name__ == "__main__":
    app.run(debug=True)
