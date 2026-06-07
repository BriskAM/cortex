import os
from flask import Flask
from flask_security import SQLAlchemyUserDatastore
from backend.app.config import DevConfig, ProdConfig
from backend.app.extensions import db, migrate, security, cors, make_celery
from backend.app.models.user import User, Role

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        env = os.getenv("FLASK_ENV", "development")
        config_class = ProdConfig if env == "production" else DevConfig
    app.config.from_object(config_class)
    
    # Initialize CORS
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize DB and Migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Flask-Security-Too datastore
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)
    
    # Initialize Celery configuration binding
    make_celery(app)
    
    # Register blueprints
    from backend.app.api.auth import auth_bp
    from backend.app.api.gh import gh_bp
    from backend.app.api.repos import repos_bp
    from backend.app.api.chat import chat_bp
    from backend.app.api.status import status_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(gh_bp, url_prefix='/api/gh')
    app.register_blueprint(repos_bp, url_prefix='/api/repos')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(status_bp, url_prefix='/api/status')
    
    # Create tables in dev if they don't exist
    if app.config.get('DEBUG'):
        with app.app_context():
            db.create_all()
            
    return app
