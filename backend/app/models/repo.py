from datetime import datetime
from backend.app.extensions import db

class IndexedRepo(db.Model):
    __tablename__ = 'indexed_repo'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Nullable for public repos
    github_url = db.Column(db.String(255), nullable=False)
    owner = db.Column(db.String(100), nullable=False)
    repo_name = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), default='main')
    status = db.Column(db.String(50), default='pending') # pending | indexing | ready | failed
    is_public = db.Column(db.Boolean, default=True)
    chroma_collection = db.Column(db.String(100), unique=True, nullable=False)
    celery_job_id = db.Column(db.String(100), nullable=True)
    file_count = db.Column(db.Integer, default=0)
    chunk_count = db.Column(db.Integer, default=0)
    pr_count = db.Column(db.Integer, default=0)
    last_indexed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('repos', lazy='dynamic'))
