from flask import Flask, jsonify, request
from db import SessionLocal, engine
from models import Base, Job, News
from scraper import scrape_keejob
from news_scraper import scrape_mosaique_news

app = Flask(__name__)

# create database tables
Base.metadata.create_all(engine)


@app.route("/")
def home():
    return {"status": "Flask Job API Running"}


@app.route("/scrape", methods=["POST"])
def scrape_and_save():
    db = SessionLocal()
    scraped = scrape_keejob()
    added = 0

    for j in scraped:
        exists = db.query(Job).filter(Job.url == j["url"]).first()
        if exists:
            continue

        job = Job(**j)
        db.add(job)
        added += 1

    db.commit()
    db.close()

    return {"message": "Scrape completed", "new_jobs": added}


@app.route("/scrapenew", methods=["POST"])
def scrape_new_only():
    db = SessionLocal()
    added = 0
    page = 1
    found_existing = False
    count=db.query(Job).count()

    while not found_existing:
        scraped = scrape_keejob(max_pages=1, start_page=page)
        
        if not scraped:
            break

        for j in scraped:
            exists = db.query(Job).filter(Job.url == j["url"]).first()
            if exists:
                found_existing = True
                break

            job = Job(**j)
            db.add(job)
            added += 1

        db.commit()
        
        if found_existing:
            break
            
        page += 1

    db.close()

    return {"message": "New jobs scraped", "new_jobs": added, "count": count, "pages_scraped": page}


@app.route("/news/scrape", methods=["POST"])
def scrape_news():
    db = SessionLocal()
    scraped = scrape_mosaique_news()
    added = 0
    added_articles = []

    for n in scraped:
        exists = db.query(News).filter(News.url == n["url"]).first()
        if exists:
            continue

        news = News(**n)
        db.add(news)
        added += 1
        added_articles.append(n)

    db.commit()
    db.close()

    return {"message": "News scrape completed", "new_articles": added, "articles": added_articles, "total_scraped": len(scraped)}


@app.route("/news")
def list_news():
    db = SessionLocal()
    
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    query = db.query(News).order_by(News.id.desc())
    
    total = query.count()
    
    query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    
    news = query.all()
    db.close()

    return jsonify({
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [
            {
                "id": n.id,
                "title": n.title,
                "url": n.url,
                "source": n.source,
                "scraped_at": n.scraped_at
            } for n in news
        ]
    })


@app.route("/jobs")
def list_jobs():
    db = SessionLocal()
    
    # Get query parameters
    title = request.args.get('title')
    company = request.args.get('company')
    location = request.args.get('location')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    # Build query with filters
    query = db.query(Job)
    
    if title:
        query = query.filter(Job.title.ilike(f"%{title}%"))
    
    if company:
        query = query.filter(Job.company.ilike(f"%{company}%"))
    
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    
    jobs = query.all()
    db.close()

    return jsonify({
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [
            {
                "id": j.id,
                "keejob_id": j.keejob_id,
                "source": j.source,
                "title": j.title,
                "company": j.company,
                "description": j.description,
                "location": j.location,
                "url": j.url
            } for j in jobs
        ]
    })


@app.route("/jobs/<int:job_id>")
def get_job(job_id):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    db.close()

    if not job:
        return {"error": "Not found"}, 404

    return {
        "id": job.id,
        "keejob_id": job.keejob_id,
        "source": job.source,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "url": job.url,
        "description": job.description,
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
