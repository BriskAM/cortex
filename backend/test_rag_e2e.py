import os
import sys
import time
import subprocess
import requests
import json
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.repo import IndexedRepo
from backend.app.models.chat import ChatSession, Message
from backend.app.services.indexer_service import IndexerService
from backend.app.services.chroma_service import ChromaService

def setup_mock_data():
    print("Setting up mock database entry and ChromaDB collections...")
    # Initialize Flask app to interact with database and ChromaDB
    app = create_app()
    
    with app.app_context():
        # Setup tables
        db.create_all()
        
        # 1. Create a mock repository entry
        repo = IndexedRepo(
            github_url="https://github.com/test_owner/test_repo",
            owner="test_owner",
            repo_name="test_repo",
            branch="main",
            status="ready",
            is_public=True,
            chroma_collection=f"col_{uuid.uuid4().hex[:8]}",
            file_count=2,
            chunk_count=2,
            pr_count=1
        )
        db.session.add(repo)
        db.session.commit()
        
        repo_id = repo.id
        print(f"Created mock repo with ID: {repo_id}")
        
        # 2. Insert dummy chunks into ChromaDB
        indexer = IndexerService()
        chroma = ChromaService()
        
        # Code chunks
        code_chunks = [
            {
                "content": "def authenticate_user(email, password):\n    # This function verifies user password against security salt.\n    if email == 'admin@cortex.dev' and password == 'password123':\n        return True\n    return False",
                "file_path": "backend/app/api/auth.py",
                "start_line": 10,
                "end_line": 15,
                "language": "python"
            },
            {
                "content": "class JWTAuth:\n    def create_token(self, user_id):\n        # Generates JWT token with secret key and returns it.\n        return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock_token'",
                "file_path": "backend/app/utils/jwt.py",
                "start_line": 20,
                "end_line": 25,
                "language": "python"
            }
        ]
        
        print("Generating embeddings for code chunks...")
        code_embeddings = indexer.embed_chunks(code_chunks, task_type="CODE_RETRIEVAL_DOCUMENT")
        
        print("Storing code embeddings in ChromaDB...")
        chroma.store_embeddings(
            collection_name=f"repo_{repo_id}_code",
            ids=[f"code_{repo_id}_1", f"code_{repo_id}_2"],
            embeddings=code_embeddings,
            metadatas=[
                {
                    "file_path": c["file_path"],
                    "start_line": c["start_line"],
                    "end_line": c["end_line"],
                    "language": c["language"]
                }
                for c in code_chunks
            ],
            documents=[c["content"] for c in code_chunks]
        )
        
        # PR chunks
        pr_chunks = [
            {
                "content": "PR #42: feat: switch to JWT token authentication\nAuthor: rishi-dev\nMerged: 2026-06-01\nFiles: backend/app/utils/jwt.py, backend/app/api/auth.py\n\nThis PR implements JSON Web Token (JWT) auth, replacing session-based authentication.",
                "pr_number": 42,
                "pr_title": "feat: switch to JWT token authentication",
                "pr_url": "https://github.com/test_owner/test_repo/pull/42",
                "pr_author": "rishi-dev",
                "merged_at": "2026-06-01"
            }
        ]
        
        print("Generating embeddings for PR chunks...")
        pr_embeddings = indexer.embed_chunks(pr_chunks, task_type="RETRIEVAL_DOCUMENT")
        
        print("Storing PR embeddings in ChromaDB...")
        chroma.store_embeddings(
            collection_name=f"repo_{repo_id}_prs",
            ids=[f"pr_{repo_id}_42"],
            embeddings=pr_embeddings,
            metadatas=[
                {
                    "pr_number": p["pr_number"],
                    "pr_title": p["pr_title"],
                    "pr_url": p["pr_url"],
                    "pr_author": p["pr_author"],
                    "merged_at": p["merged_at"]
                }
                for p in pr_chunks
            ],
            documents=[p["content"] for p in pr_chunks]
        )
        
        # 3. Create a ChatSession
        session = ChatSession(
            repo_id=repo_id,
            scope="repo",
            title="New Chat Session"
        )
        db.session.add(session)
        db.session.commit()
        
        session_id = session.id
        print(f"Created chat session with ID: {session_id}")
        
        return repo_id, session_id

def cleanup_data(repo_id, session_id):
    print(f"Cleaning up DB entries and ChromaDB collections for repo {repo_id}...")
    app = create_app()
    with app.app_context():
        # Delete ChatSession & Messages (cascaded delete-orphan handles message deletion)
        session = db.session.get(ChatSession, session_id)
        if session:
            db.session.delete(session)
            
        repo = db.session.get(IndexedRepo, repo_id)
        if repo:
            db.session.delete(repo)
            
        db.session.commit()
        
        # Delete ChromaDB collections
        chroma = ChromaService()
        chroma.delete_collection(f"repo_{repo_id}_code")
        chroma.delete_collection(f"repo_{repo_id}_prs")
        print("Cleanup completed.")

def test_rag():
    # Setup data
    repo_id, session_id = setup_mock_data()
    
    print("\nStarting Flask server for E2E RAG test...")
    # Start Flask dev server in a background process
    server_process = subprocess.Popen(
        [sys.executable, "backend/run.py"],
        env={
            "PYTHONPATH": ".",
            "FLASK_ENV": "development",
            "PORT": "5002",
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"
        }
    )
    
    # Wait for server to start up
    time.sleep(3)
    
    base_url = f"http://127.0.0.1:5002/api/chat/sessions/{session_id}/message"
    
    try:
        print("\nSending POST request to RAG SSE endpoint...")
        # Stream response
        response = requests.post(
            base_url,
            json={"content": "Explain how authentication and token creation works"},
            stream=True
        )
        
        print(f"Response Status Code: {response.status_code}")
        assert response.status_code == 200, "RAG SSE request failed"
        
        print("\n--- STREAMED RESPONSE ---")
        has_tokens = False
        has_done = False
        sources = None
        full_text = ""
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    data_json = json.loads(decoded_line[6:])
                    if "token" in data_json:
                        token = data_json["token"]
                        print(token, end="", flush=True)
                        full_text += token
                        has_tokens = True
                    elif "done" in data_json and data_json["done"] is True:
                        has_done = True
                        sources = data_json.get("sources")
                        print("\n\n[Done event received]")
        
        print("\n--- VERIFICATION ---")
        assert has_tokens, "No tokens received from LLM stream"
        assert has_done, "No 'done' event received"
        assert sources is not None, "Sources should not be None"
        print(f"Number of retrieved sources cited: {len(sources)}")
        for src in sources:
            print(f"- Type: {src['type']}, File/PR: {src.get('file') or src.get('pr_number')}")
            
        assert len(sources) > 0, "No sources retrieved and cited"
        
        # Verify persistence
        print("\nVerifying message persistence in DB...")
        app = create_app()
        with app.app_context():
            messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at.asc()).all()
            print(f"Persisted messages: {len(messages)}")
            assert len(messages) == 2, "Expected exactly 2 messages (user + assistant)"
            
            user_msg = messages[0]
            asst_msg = messages[1]
            
            assert user_msg.role == "user"
            assert user_msg.content == "Explain how authentication and token creation works"
            
            assert asst_msg.role == "assistant"
            assert len(asst_msg.content) > 0
            assert asst_msg.sources == sources
            
            # Check if session title was updated
            session = db.session.get(ChatSession, session_id)
            print(f"Updated session title: '{session.title}'")
            assert session.title != "New Chat Session", "Session title should have been updated"
            
        print("\nE2E RAG Pipeline test passed successfully!")
        
    except Exception as e:
        print(f"\nE2E RAG Test failed: {e}")
        server_process.terminate()
        cleanup_data(repo_id, session_id)
        sys.exit(1)
        
    finally:
        print("\nStopping Flask server...")
        server_process.terminate()
        server_process.wait()
        cleanup_data(repo_id, session_id)

if __name__ == '__main__':
    test_rag()
