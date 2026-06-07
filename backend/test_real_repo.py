import os
import sys
import uuid
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.repo import IndexedRepo
from backend.app.models.chat import ChatSession, Message
from backend.app.tasks.indexing_tasks import index_repository
from backend.app.services.rag_service import RAGService
from backend.app.services.chroma_service import ChromaService

def get_github_token():
    # Try getting GITHUB_TOKEN from env first
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token
    # Try calling gh auth token
    try:
        token = subprocess.check_output(["gh", "auth", "token"]).decode('utf-8').strip()
        return token
    except Exception:
        return None

def main():
    owner = "BriskAM"
    repo_name = "resume" # Small repository for quick indexing
    
    if len(sys.argv) > 2:
        owner = sys.argv[1]
        repo_name = sys.argv[2]
        
    print(f"Target repository: {owner}/{repo_name}")
    
    # Check GITHUB_TOKEN
    token = get_github_token()
    if not token:
        print("ERROR: GitHub token not found. Please log in with `gh auth login` or set GITHUB_TOKEN.")
        sys.exit(1)
    
    # Expose token to environment
    os.environ["GITHUB_TOKEN"] = token
    
    app = create_app()
    
    with app.app_context():
        db.create_all()
        
        # Clean up any existing database and ChromaDB collections from previous test runs to start fresh
        existing = IndexedRepo.query.filter_by(owner=owner, repo_name=repo_name).first()
        if existing:
            print(f"Cleaning up pre-existing repository data for {owner}/{repo_name}...")
            chroma = ChromaService()
            chroma.delete_collection(f"repo_{existing.id}_code")
            chroma.delete_collection(f"repo_{existing.id}_prs")
            # Delete sessions
            sessions = ChatSession.query.filter_by(repo_id=existing.id).all()
            for s in sessions:
                # Delete messages first
                Message.query.filter_by(session_id=s.id).delete()
                db.session.delete(s)
            db.session.delete(existing)
            db.session.commit()

        # Query repository details from GitHub to resolve the correct default branch
        from backend.app.services.github_service import GitHubService
        gh_service = GitHubService(token=token)
        try:
            repo_details = gh_service.get_repo_details(owner, repo_name)
            default_branch = repo_details.get("default_branch", "main")
            print(f"Resolved default branch: '{default_branch}'")
        except Exception as e:
            print(f"Failed to query repository from GitHub API: {e}")
            sys.exit(1)

        # Insert repository metadata with resolved branch
        repo = IndexedRepo(
            github_url=f"https://github.com/{owner}/{repo_name}",
            owner=owner,
            repo_name=repo_name,
            branch=default_branch,
            status="pending",
            is_public=True,
            chroma_collection=f"col_{uuid.uuid4().hex[:8]}"
        )
        db.session.add(repo)
        db.session.commit()
        print(f"Inserted repository {owner}/{repo_name} into DB with branch '{default_branch}'.")
            
        repo_id = repo.id
        
        # Run indexing pipeline
        print(f"Running repository indexing task for ID {repo_id}...")
        result = index_repository(repo_id)
        print("Indexing completed. Result status:", result)
        
        db.session.refresh(repo)
            
        print("\n--- REPOSITORY DETAILS ---")
        print(f"ID: {repo.id}")
        print(f"Status: {repo.status}")
        print(f"Files: {repo.file_count}")
        print(f"Chunks: {repo.chunk_count}")
        print(f"PRs: {repo.pr_count}")
        
        if repo.status != "ready":
            print("ERROR: Repository indexing failed.")
            sys.exit(1)
            
        # Create a ChatSession
        session = ChatSession(
            repo_id=repo.id,
            scope="repo",
            title="Console Test Session"
        )
        db.session.add(session)
        db.session.commit()
        session_id = session.id
        print(f"\nCreated chat session with ID: {session_id}")
        
        # Define test query
        query = "Explain the structure of this repository and summarize what it does."
        print(f"\nQuerying RAG: '{query}'")
        
        rag = RAGService()
        generator = rag.query_rag(
            repo_id=repo_id,
            session_id=session_id,
            user_message=query,
            scope="repo"
        )
        
        print("\n--- STREAMED RAG RESPONSE ---")
        full_response = ""
        sources = []
        for token, retrieved_sources in generator:
            print(token, end="", flush=True)
            full_response += token
            sources = retrieved_sources
            
        print("\n\n--- CITATIONS & SOURCES ---")
        print(f"Total Sources Cited: {len(sources)}")
        for idx, src in enumerate(sources):
            if src["type"] == "code":
                print(f"[{idx+1}] Code File: {src['file']} (Lines {src['start_line']}-{src['end_line']})")
            else:
                print(f"[{idx+1}] PR #{src['pr_number']}: {src['pr_title']} (Author: {src['pr_author']}, Merged: {src['merged_at']})")
                
        # Persist messages
        user_msg = Message(session_id=session_id, role="user", content=query)
        assistant_msg = Message(session_id=session_id, role="assistant", content=full_response, sources=sources)
        db.session.add(user_msg)
        db.session.add(assistant_msg)
        db.session.commit()
        print("\nTest session messages persisted successfully in DB.")
        print(f"To run interactive chat, start the web interface!")

if __name__ == '__main__':
    main()
