import os
import sys
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.repo import IndexedRepo
from backend.app.tasks.indexing_tasks import index_repository
from backend.app.services.chroma_service import ChromaService

def test_indexing():
    print("Initializing Flask App context...")
    app = create_app()
    
    with app.app_context():
        # Setup tables
        db.create_all()
        
        # Check if environment variables are set
        github_token = os.getenv("GITHUB_TOKEN")
        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        print(f"GITHUB_TOKEN present: {bool(github_token)}")
        print(f"GOOGLE_API_KEY present: {bool(google_api_key)}")
        
        if not github_token:
            print("WARNING: GITHUB_TOKEN is not set. The E2E test will fail unless a mock token or token bypass is used.")
            print("Please make sure you have GITHUB_TOKEN set in your environment or active keyring.")
            
        # Create a mock repo entry
        # We index a small public repo or a mock representation. Let's try indexing 'BriskAM/cortex'
        repo = IndexedRepo(
            github_url="https://github.com/BriskAM/cortex",
            owner="BriskAM",
            repo_name="cortex",
            branch="main",
            status="pending",
            is_public=True,
            chroma_collection=f"col_{uuid.uuid4().hex[:8]}"
        )
        db.session.add(repo)
        db.session.commit()
        
        repo_id = repo.id
        print(f"Created mock repository in DB with ID: {repo_id}")
        
        try:
            print("Running index_repository task synchronously...")
            # We run it synchronously by calling it directly, not via .delay()
            result = index_repository(repo_id)
            print("Task Result:", result)
            
            # Fetch repo from DB
            db.session.refresh(repo)
            
            print("\n--- VERIFICATION STATS ---")
            print(f"Status: {repo.status}")
            print(f"Files: {repo.file_count}")
            print(f"Chunks: {repo.chunk_count}")
            print(f"PRs: {repo.pr_count}")
            print(f"Last Indexed: {repo.last_indexed_at}")
            
            assert repo.status == "ready", "Repo status should be 'ready'"
            assert repo.file_count > 0, "File count should be greater than 0"
            assert repo.chunk_count > 0, "Chunk count should be greater than 0"
            
            # Verify ChromaDB
            chroma = ChromaService()
            code_col = chroma.get_or_create_collection(f"repo_{repo_id}_code")
            print(f"ChromaDB code collection item count: {code_col.count()}")
            assert code_col.count() == repo.chunk_count, "ChromaDB count should match chunk count"
            
            print("\nE2E Indexing Pipeline test passed successfully!")
            
        except Exception as e:
            print(f"\nE2E Indexing Pipeline test failed: {e}")
            sys.exit(1)
        finally:
            # Cleanup DB and ChromaDB
            print("Cleaning up test resources...")
            try:
                db.session.delete(repo)
                db.session.commit()
                chroma = ChromaService()
                chroma.delete_collection(f"repo_{repo_id}_code")
                chroma.delete_collection(f"repo_{repo_id}_prs")
            except Exception as ex:
                print(f"Cleanup error: {ex}")

if __name__ == '__main__':
    test_indexing()
