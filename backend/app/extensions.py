from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_security import Security
from flask_cors import CORS
from celery import Celery

db = SQLAlchemy()
migrate = Migrate()
security = Security()
cors = CORS()

# Create a Celery instance with name 'cortex'
celery = Celery('cortex')

def make_celery(app):
    """Binds Flask app configuration to Celery instance and context."""
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_ignore_result=True
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
                
    celery.Task = ContextTask
    return celery
