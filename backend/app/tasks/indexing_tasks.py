from backend.app.extensions import celery
from backend.app.extensions import db
from backend.app.models.repo import IndexedRepo
import time

@celery.task(bind=True)
def index_repository(self, repo_id):
    """
    Celery task that runs the indexing pipeline for a repository:
    1. Fetch file tree and file contents.
    2. Parse and chunk code files.
    3. Fetch and chunk merged pull requests.
    4. Generate embeddings for all chunks.
    5. Store in ChromaDB.
    6. Update database repository status.
    """
    print(f"Starting indexing for repo {repo_id}")
    # Simulate work with state progress updates
    stages = [
        {"stage": "fetching_files", "progress": 5},
        {"stage": "chunking_code", "progress": 20},
        {"stage": "fetching_prs", "progress": 50},
        {"stage": "embedding", "progress": 70},
        {"stage": "storing", "progress": 90},
        {"stage": "done", "progress": 100}
    ]
    
    for stage_info in stages:
        # Update Celery state progress
        self.update_state(
            state='PROGRESS',
            meta={
                'stage': stage_info['stage'],
                'progress': stage_info['progress']
            }
        )
        time.sleep(1)
        
    return {"status": "SUCCESS"}
