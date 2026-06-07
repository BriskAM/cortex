from flask import Blueprint, jsonify, request

gh_bp = Blueprint('gh', __name__)

@gh_bp.route('/<owner>/<repo>', methods=['GET'])
def get_repo_status(owner, repo):
    """
    Resolve repo by owner + name.
    Triggers indexing via Celery if first time seen.
    """
    # Mocking status check: e.g. return indexing/ready/not_found
    # For now, return ready if repo is 'cortex' else indexing stub
    if owner.lower() == "briskam" and repo.lower() == "cortex":
        return jsonify({
            "status": "ready",
            "repo_id": 1,
            "file_count": 42,
            "chunk_count": 256,
            "pr_count": 12
        }), 200
        
    return jsonify({
        "status": "indexing",
        "progress": 42,
        "job_id": "mock-celery-job-uuid-1234"
    }), 200

@gh_bp.route('/<owner>/<repo>/pr/<int:number>', methods=['GET'])
def get_pr_status(owner, repo, number):
    """
    Resolve specific PR.
    """
    return jsonify({
        "status": "ready",
        "pr_number": number,
        "pr_title": f"feat: add support for {repo} PR indexing",
        "pr_body": "This is a mock description of the pull request.",
        "pr_author": "developer-guy",
        "merged_at": "2026-06-07T12:00:00Z",
        "files_changed": ["backend/app/api/gh.py", "frontend/src/views/PrView.vue"]
    }), 200
