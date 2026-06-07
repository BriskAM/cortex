from flask import Blueprint, jsonify

status_bp = Blueprint('status', __name__)

@status_bp.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    Get progress and status details for a running Celery indexing job.
    """
    # Return mock progress structure
    return jsonify({
        "status": "indexing",
        "progress": 50,
        "stage": "fetching_prs",
        "error": None
    }), 200
