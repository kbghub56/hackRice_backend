from flask import Flask, jsonify
from flask_cors import CORS
import requests
from transformers import pipeline
from flask_sqlalchemy import SQLAlchemy
import os
from bs4 import BeautifulSoup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsdb.sqlite3'
db = SQLAlchemy(app)

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

@app.route('/get-stored-articles', methods=['GET'])
def get_stored_articles():
    articles = Article.query.all()
    return jsonify([{
        "title": article.title,
        "summary": article.summary,
        "url": article.url,
        "image_url": article.image_url,
        "keyword": article.keyword
    } for article in articles])

def fetch_articles(keywords):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    all_articles = []

    for keyword in keywords:
        params = {
            "q": keyword,
            "language": "en",
            "pageSize": 1  # Fetching 5 articles per keyword; adjust as needed
        }

        response = requests.get(API_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()

        articles_for_keyword = response.json().get('articles', [])
        
        # Add the keyword to each article's data
        for article in articles_for_keyword:
            article['keyword'] = keyword
        
        all_articles.extend(articles_for_keyword)

    return all_articles

def get_full_article_content(url): #helper function for summarize_articles. scrapes content from article. 
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        article_content = ' '.join(para.text for para in paragraphs)
        return article_content
    except Exception as e:
        print(f"Error fetching full content for {url}: {e}")
        return None
    
def summarize_articles(articles):
    summarized_articles = []

    for article in articles:
        title = article.get("title")
        content = article.get("content", "")
        url = article.get("url")
        image_url = article.get("urlToImage")  # Extract the image URL
        keyword = article.get("keyword")

        content = get_full_article_content(url)

        if not content:
            continue

        summary = summarizer(content, max_length=300, min_length=100, do_sample=True)[0]['summary_text']

        # Check if the article already exists in the database
        existing_article = Article.query.filter_by(url=url).first()

        if not existing_article:
            article_entry = Article(title=title, summary=summary, url=url, image_url=image_url, keyword=keyword)
            db.session.add(article_entry)
            db.session.commit()

        summarized_articles.append({
            "title": title,
            "summary": summary,
            "url": url,
            "image_url": image_url,  # Add the image URL to the summarized article data
            "keyword" : keyword 
        })

    return summarized_articles

#Define Database Model

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    keyword = db.Column(db.String(100), nullable=False)

with app.app_context():
        db.create_all()

if __name__ == "__main__":
    app.run(debug=True)



