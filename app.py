from flask import Flask, jsonify
from flask_cors import CORS
from transformers import pipeline
from flask_sqlalchemy import SQLAlchemy
from newsdataapi import NewsDataApiClient

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsdb.sqlite3'
db = SQLAlchemy(app)

# Initialize the summarizer
summarizer = pipeline("summarization")

# Constants
api = NewsDataApiClient(apikey="pub_2999839b534cd154687eeb2e90f72d19aec9d") # Replace with your actual NewsAPI key
HARDCODED_KEYWORDS = ["Sustainability", "Legal", "Energy"]  # You can change or add more keywords

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
        "summary": article.summary,  # Use 'description' instead of 'summary'
        "url": article.url,                # Use 'link' instead of 'url'
        "image_url": article.image_url,      # This remains the same
        "creator": article.creator,
        "description": article.description        # Use 'keywords' which is a list, instead of a single 'keyword'
    } for article in articles])


def fetch_articles(keywords):
    all_articles = []

    for keyword in keywords:
        response = api.news_api(q=keyword)["results"]
        
        # Assuming 'response' is a list of articles
        articles_for_keyword = response[:3]  # Limit to 2 articles


        all_articles.extend(articles_for_keyword)

    return all_articles

    
def summarize_articles(articles):
    summarized_articles = []

    for article in articles:
        title = article.get("title")
        description = article.get("description")
        content = article.get("content")
        url = article.get("link")
        image_url = article.get("image_url")  # Extract the image URL
        if(article.get("creator"))!=None:
            creator = str(article.get("creator"))
        else:
            creator = "None"


        if not content:
            continue
        
        content = content[:500]

        summary = summarizer(content, max_length=800, min_length=50, do_sample=False)[0]['summary_text']
        if len(description)>220:
            description = summarizer(content, max_length=220, min_length=40, do_sample=False)[0]['summary_text']

        # Check if the article already exists in the database
        existing_article = Article.query.filter_by(url=url).first()

        if not existing_article:
            article_entry = Article(title=title, summary=summary, url=url, image_url=image_url, creator=creator, description = description)
            db.session.add(article_entry)
            db.session.commit()

        summarized_articles.append({
            "title": title,
            "summary": summary,
            "url": url,
            "image_url": image_url,
            "creator" : creator,
            "description" : description
        })

    return summarized_articles


#Define Database Model

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    creator = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable = False)

with app.app_context():
        db.create_all()

if __name__ == "__main__":
    app.run(debug=True)



