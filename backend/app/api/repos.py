from flask import Blueprint, jsonify

repos_bp = Blueprint('repos', __name__)

@repos_bp.route('/', methods=['GET'])
def list_repos():
    """List user's saved repos."""
    return jsonify([
        {
            "id": 1,
            "owner": "BriskAM",
            "repo_name": "cortex",
            "github_url": "https://github.com/BriskAM/cortex",
            "branch": "main",
            "status": "ready",
            "file_count": 42,
            "chunk_count": 256,
            "pr_count": 12,
            "last_indexed_at": "2026-06-07T12:00:00Z"
        }
    ]), 200

@repos_bp.route('/<int:repo_id>', methods=['DELETE'])
def delete_repo(repo_id):
    """Delete repo and associated Chroma collections."""
    return jsonify({
        "message": f"Repository {repo_id} deleted successfully"
    }), 200

@repos_bp.route('/<int:repo_id>/reindex', methods=['POST'])
def reindex_repo(repo_id):
    """Re-trigger full indexing Celery task."""
    return jsonify({
        "message": "Re-indexing triggered successfully",
        "job_id": "mock-reindex-job-uuid-5678"
    }), 202
