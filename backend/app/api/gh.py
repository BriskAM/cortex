import uuid
from flask import Blueprint, jsonify, request, current_app
from flask_security import current_user
from backend.app.extensions import db
from backend.app.models.repo import IndexedRepo
from backend.app.services.github_service import GitHubService
from backend.app.tasks.indexing_tasks import index_repository

gh_bp = Blueprint('gh', __name__)

@gh_bp.route('/<owner>/<repo>', methods=['GET'])
def get_repo_status(owner, repo):
    """
    Resolve repo by owner + name.
    Triggers indexing via Celery if first time seen.
    """
    # 1. Search DB for repo
    repo_obj = IndexedRepo.query.filter(
        db.func.lower(IndexedRepo.owner) == owner.lower(),
        db.func.lower(IndexedRepo.repo_name) == repo.lower()
    ).first()
    
    # Get GITHUB_TOKEN from current_user or env/config
    token = None
    if current_user and current_user.is_authenticated:
        token = current_user.github_token
    if not token:
        token = current_app.config.get("GITHUB_TOKEN")
        
    if repo_obj:
        if repo_obj.status == "ready":
            return jsonify({
                "status": "ready",
                "repo_id": repo_obj.id,
                "file_count": repo_obj.file_count,
                "chunk_count": repo_obj.chunk_count,
                "pr_count": repo_obj.pr_count
            }), 200
        elif repo_obj.status == "indexing" or repo_obj.status == "pending":
            return jsonify({
                "status": "indexing",
                "progress": 0,
                "job_id": repo_obj.celery_job_id,
                "repo_id": repo_obj.id
            }), 200
        else:
            # If failed, re-trigger indexing
            try:
                gh_service = GitHubService(token=token)
                repo_details = gh_service.get_repo_details(owner, repo)
            except Exception as e:
                return jsonify({"status": "not_found", "error": f"Failed to check GitHub: {str(e)}"}), 404
                
            repo_obj.status = "pending"
            db.session.commit()
            
            job = index_repository.delay(repo_obj.id)
            repo_obj.status = "indexing"
            repo_obj.celery_job_id = job.id
            db.session.commit()
            
            return jsonify({
                "status": "indexing",
                "progress": 0,
                "job_id": job.id,
                "repo_id": repo_obj.id
            }), 200

    # 2. Not seen yet
    try:
        gh_service = GitHubService(token=token)
        repo_details = gh_service.get_repo_details(owner, repo)
        default_branch = repo_details.get("default_branch", "main")
    except Exception as e:
        return jsonify({"status": "not_found", "error": str(e)}), 404

    # Create IndexedRepo metadata record
    repo_obj = IndexedRepo(
        user_id=current_user.id if (current_user and current_user.is_authenticated) else None,
        github_url=repo_details["html_url"],
        owner=repo_details["owner"],
        repo_name=repo_details["name"],
        branch=default_branch,
        status="pending",
        is_public=True,
        chroma_collection=f"col_{uuid.uuid4().hex[:8]}"
    )
    db.session.add(repo_obj)
    db.session.commit()

    # Trigger indexing task
    job = index_repository.delay(repo_obj.id)
    
    # Store celery_job_id
    repo_obj.status = "indexing"
    repo_obj.celery_job_id = job.id
    db.session.commit()

    return jsonify({
        "status": "indexing",
        "progress": 0,
        "job_id": job.id,
        "repo_id": repo_obj.id
    }), 200

@gh_bp.route('/<owner>/<repo>/pr/<int:number>', methods=['GET'])
def get_pr_status(owner, repo, number):
    """
    Resolve specific PR.
    """
    repo_obj = IndexedRepo.query.filter(
        db.func.lower(IndexedRepo.owner) == owner.lower(),
        db.func.lower(IndexedRepo.repo_name) == repo.lower()
    ).first()
    
    if not repo_obj:
        return jsonify({"error": "Repository not found or not indexed yet"}), 404
        
    token = None
    if current_user and current_user.is_authenticated:
        token = current_user.github_token
    if not token:
        token = current_app.config.get("GITHUB_TOKEN")
        
    try:
        gh_service = GitHubService(token=token)
        pr_details = gh_service.get_pr_details(owner, repo_obj.repo_name, number)
        pr_details["status"] = "ready"
        pr_details["repo_id"] = repo_obj.id
        return jsonify(pr_details), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch PR details: {str(e)}"}), 500
