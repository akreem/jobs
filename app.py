from flask import Flask, jsonify, request
from db import SessionLocal, engine
from models import Base, Job
from scraper import scrape_keejob

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
