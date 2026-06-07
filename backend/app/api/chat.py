from flask import Blueprint, jsonify, request, Response, current_app, stream_with_context
from backend.app.extensions import db
from backend.app.models.chat import ChatSession, Message
from backend.app.models.repo import IndexedRepo
from backend.app.services.rag_service import RAGService
import json

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """List sessions for a specific repo_id."""
    repo_id = request.args.get('repo_id', type=int)
    if not repo_id:
        return jsonify({"error": "repo_id is required"}), 400
        
    sessions = ChatSession.query.filter_by(repo_id=repo_id).order_by(ChatSession.created_at.desc()).all()
    return jsonify([
        {
            "id": s.id,
            "repo_id": s.repo_id,
            "title": s.title,
            "scope": s.scope,
            "pr_number": s.pr_number,
            "created_at": s.created_at.isoformat()
        } for s in sessions
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
        
    # Check if repo exists
    repo = db.session.get(IndexedRepo, repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404
        
    title = f"PR #{pr_number} Chat" if scope == "pr" else "New Chat Session"
    
    session = ChatSession(
        repo_id=repo_id,
        scope=scope,
        pr_number=pr_number,
        title=title
    )
    
    try:
        db.session.add(session)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create session: {str(e)}"}), 500
        
    return jsonify({
        "id": session.id,
        "repo_id": session.repo_id,
        "scope": session.scope,
        "pr_number": session.pr_number,
        "title": session.title,
        "created_at": session.created_at.isoformat()
    }), 201

@chat_bp.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """Retrieve session details and history."""
    session = db.session.get(ChatSession, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at.asc()).all()
    
    return jsonify({
        "id": session.id,
        "repo_id": session.repo_id,
        "scope": session.scope,
        "pr_number": session.pr_number,
        "title": session.title,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
                "created_at": m.created_at.isoformat()
            } for m in messages
        ]
    }), 200

@chat_bp.route('/sessions/<int:session_id>/message', methods=['GET', 'POST'])
def send_message(session_id):
    """Send message to a session and get SSE stream response."""
    session = db.session.get(ChatSession, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    # Extract user query depending on method
    if request.method == 'POST':
        data = request.get_json() or {}
        user_message = data.get('content', '')
    else:
        user_message = request.args.get('q', '')

    if not user_message:
        return jsonify({"error": "Query message content is required"}), 400
        
    rag_service = RAGService()
    
    # Extract app instance while context is active in the request thread
    app = current_app._get_current_object()
    
    def generate():
        with app.app_context():
            assistant_content = ""
            sources = []
            
            # Invoke RAG generator
            generator = rag_service.query_rag(
                repo_id=session.repo_id,
                session_id=session_id,
                user_message=user_message,
                scope=session.scope,
                pr_number=session.pr_number
            )
            
            for token, retrieved_sources in generator:
                assistant_content += token
                sources = retrieved_sources
                yield f"data: {json.dumps({'token': token})}\n\n"
                
            # Post-stream persistence
            try:
                thread_session = db.session.get(ChatSession, session_id)
                user_msg = Message(
                    session_id=session_id,
                    role="user",
                    content=user_message
                )
                assistant_msg = Message(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_content,
                    sources=sources
                )
                db.session.add(user_msg)
                db.session.add(assistant_msg)
                
                # Auto update session title if default
                if thread_session and (not thread_session.title or thread_session.title == "New Chat Session" or thread_session.title.startswith("PR #")):
                    thread_session.title = user_message[:30] + ("..." if len(user_message) > 30 else "")
                    
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Failed to persist chat messages: {e}")
                
            # Final Event
            yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"
        
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@chat_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a chat session."""
    session = db.session.get(ChatSession, session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    try:
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": "Session deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete session: {str(e)}"}), 500
