from flask import Blueprint, jsonify, request
from backend.app.extensions import db
from backend.app.models.repo import IndexedRepo
from backend.app.models.chat import ChatSession, Message
from backend.app.services.chroma_service import ChromaService
from backend.app.tasks.indexing_tasks import index_repository

repos_bp = Blueprint('repos', __name__)

@repos_bp.route('/', methods=['GET'])
def list_repos():
    """List indexed repositories."""
    repos = IndexedRepo.query.order_by(IndexedRepo.created_at.desc()).all()
    return jsonify([
        {
            "id": r.id,
            "owner": r.owner,
            "repo_name": r.repo_name,
            "github_url": r.github_url,
            "branch": r.branch,
            "status": r.status,
            "file_count": r.file_count,
            "chunk_count": r.chunk_count,
            "pr_count": r.pr_count,
            "last_indexed_at": r.last_indexed_at.isoformat() if r.last_indexed_at else None,
            "created_at": r.created_at.isoformat()
        } for r in repos
    ]), 200

@repos_bp.route('/<int:repo_id>', methods=['DELETE'])
def delete_repo(repo_id):
    """Delete repo and associated Chroma collections and database chat histories."""
    repo = db.session.get(IndexedRepo, repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404
        
    try:
        # 1. Clean up associated chat messages & sessions first
        sessions = ChatSession.query.filter_by(repo_id=repo_id).all()
        for session in sessions:
            Message.query.filter_by(session_id=session.id).delete()
            db.session.delete(session)
            
        # 2. Delete ChromaDB collections
        chroma = ChromaService()
        chroma.delete_collection(f"repo_{repo_id}_code")
        chroma.delete_collection(f"repo_{repo_id}_prs")
        
        # 3. Delete repository row
        db.session.delete(repo)
        db.session.commit()
        
        return jsonify({
            "message": f"Repository {repo_id} deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete repository: {str(e)}"}), 500

@repos_bp.route('/<int:repo_id>/reindex', methods=['POST'])
def reindex_repo(repo_id):
    """Re-trigger full indexing Celery task."""
    repo = db.session.get(IndexedRepo, repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404
        
    try:
        # Trigger Celery task asynchronously
        job = index_repository.delay(repo_id)
        
        # Update repository status and celery job ID
        repo.status = "indexing"
        repo.celery_job_id = job.id
        db.session.commit()
        
        return jsonify({
            "message": "Re-indexing triggered successfully",
            "job_id": job.id
        }), 202
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to trigger reindexing: {str(e)}"}), 500
