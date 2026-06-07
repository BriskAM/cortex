from flask import Blueprint, jsonify, request, Response
import time
import json

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """List sessions for a specific repo_id."""
    repo_id = request.args.get('repo_id', type=int)
    if not repo_id:
        return jsonify({"error": "repo_id is required"}), 400
        
    return jsonify([
        {
            "id": 1,
            "repo_id": repo_id,
            "title": "Explain user authentication flow",
            "scope": "repo",
            "created_at": "2026-06-07T12:05:00Z"
        }
    ]), 200

@chat_bp.route('/sessions', methods=['POST'])
def create_session():
    """Create a new chat session."""
    data = request.get_json() or {}
    repo_id = data.get('repo_id')
    scope = data.get('scope', 'repo')
    pr_number = data.get('pr_number')
    
    if not repo_id:
        return jsonify({"error": "repo_id is required"}), 400
        
    return jsonify({
        "id": 1,
        "repo_id": repo_id,
        "scope": scope,
        "pr_number": pr_number,
        "title": f"Session for PR #{pr_number}" if scope == "pr" else "New Chat Session",
        "created_at": "2026-06-07T12:10:00Z"
    }), 201

@chat_bp.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """Retrieve session details and history."""
    return jsonify({
        "id": session_id,
        "repo_id": 1,
        "scope": "repo",
        "title": "Explain user authentication flow",
        "messages": [
            {
                "id": 1,
                "role": "user",
                "content": "Where is auth handled?",
                "created_at": "2026-06-07T12:05:00Z"
            },
            {
                "id": 2,
                "role": "assistant",
                "content": "Authentication is handled in `backend/app/api/auth.py` and configuration is in `backend/app/config.py`.",
                "sources": [
                    {"type": "code", "file": "backend/app/api/auth.py", "start_line": 1, "end_line": 20, "snippet": "..."}
                ],
                "created_at": "2026-06-07T12:05:02Z"
            }
        ]
    }), 200

@chat_bp.route('/sessions/<int:session_id>/message', methods=['POST'])
def send_message(session_id):
    """Send message to a session and get SSE stream response."""
    data = request.get_json() or {}
    user_message = data.get('content', '')
    
    def generate():
        # Yield a sequence of mock tokens simulating thinking and streaming
        tokens = ["This", " is", " a", " simulated", " response", " to", " your", " query", ":", f" '{user_message}'"]
        for token in tokens:
            time.sleep(0.1)
            yield f"data: {json.dumps({'token': token})}\n\n"
            
        # Yield final sources payload
        sources = [
            {
                "type": "code",
                "file": "backend/app/api/auth.py",
                "start_line": 1,
                "end_line": 10,
                "snippet": "# Auth blueprint skeleton"
            }
        ]
        yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"
        
    return Response(generate(), mimetype='text/event-stream')

@chat_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a chat session."""
    return jsonify({
        "message": f"Session {session_id} deleted successfully"
    }), 200
