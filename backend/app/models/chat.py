from datetime import datetime
from backend.app.extensions import db

class ChatSession(db.Model):
    __tablename__ = 'chat_session'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Nullable for anonymous/public chat
    repo_id = db.Column(db.Integer, db.ForeignKey('indexed_repo.id'), nullable=False)
    scope = db.Column(db.String(50), default='repo') # "repo" | "pr"
    pr_number = db.Column(db.Integer, nullable=True) # Set if scope == "pr"
    title = db.Column(db.String(255), nullable=True) # Auto-generated from first message
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('chat_sessions', lazy='dynamic'))
    repo = db.relationship('IndexedRepo', backref=db.backref('chat_sessions', lazy='dynamic'))

class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False) # "user" | "assistant"
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.JSON, nullable=True) # JSON list of sources cited
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    session = db.relationship('ChatSession', backref=db.backref('messages', cascade='all, delete-orphan', lazy='dynamic'))
