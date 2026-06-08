from flask import Blueprint, jsonify
from celery.result import AsyncResult
from backend.app.extensions import celery

status_bp = Blueprint('status', __name__)

@status_bp.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    Get progress and status details for a running Celery indexing job.
    """
    res = AsyncResult(job_id, app=celery)
    state = res.state
    info = res.info
    
    stage = "fetching_files"
    progress = 0
    error = None
    
    if state == "SUCCESS":
        stage = "done"
        progress = 100
    elif state == "FAILURE":
        stage = "failed"
        progress = 0
        error = str(info)
    elif state == "PROGRESS":
        if isinstance(info, dict):
            stage = info.get("stage", "fetching_files")
            progress = info.get("progress", 0)
    elif isinstance(info, dict):
        stage = info.get("stage", stage)
        progress = info.get("progress", progress)
        error = info.get("error", None)

    return jsonify({
        "status": state,
        "progress": progress,
        "stage": stage,
        "error": error
    }), 200
