from datetime import datetime
from backend.app.extensions import celery, db
from backend.app.models.repo import IndexedRepo
from backend.app.services.github_service import GitHubService
from backend.app.services.indexer_service import IndexerService
from backend.app.services.pr_service import PRService
from backend.app.services.chroma_service import ChromaService

@celery.task(bind=True)
def index_repository(self, repo_id):
    """
    Celery task that runs the indexing pipeline for a repository:
    1. Fetch file tree and file contents.
    2. Parse and chunk code files.
    3. Fetch and chunk merged pull requests.
    4. Generate embeddings for all chunks.
    5. Store in ChromaDB.
    6. Update database repository status.
    """
    print(f"Starting Celery indexing job for repo_id: {repo_id}")
    
    # Use app context database session
    repo = db.session.get(IndexedRepo, repo_id)
    if not repo:
        error_msg = f"Repository with id {repo_id} not found in database"
        print(error_msg)
        return {"error": error_msg}

    def update_progress(state, stage, progress):
        if self.request.id:
            self.update_state(state=state, meta={'stage': stage, 'progress': progress})

    # Retrieve user specific github token if configured, else fallback to server-wide env token
    user_token = None
    if repo.user and repo.user.github_token:
         user_token = repo.user.github_token
         
    # Initialize services
    github_service = GitHubService(token=user_token)
    indexer_service = IndexerService()
    pr_service = PRService(github_service)
    chroma_service = ChromaService()

    try:
        # Update repo status to indexing
        repo.status = "indexing"
        db.session.commit()

        # --- STEP 1: FETCH FILES ---
        update_progress('PROGRESS', 'fetching_files', 5)
        print(f"[{repo.owner}/{repo.repo_name}] Fetching git tree...")
        file_tree = github_service.fetch_file_tree(repo.owner, repo.repo_name, repo.branch)
        
        # --- STEP 2: CHUNK CODE ---
        update_progress('PROGRESS', 'chunking_code', 20)
        print(f"[{repo.owner}/{repo.repo_name}] Parsing and chunking code files...")
        code_chunks = []
        for idx, file_info in enumerate(file_tree):
            path = file_info["path"]
            content = github_service.fetch_file_content(repo.owner, repo.repo_name, path, repo.branch)
            file_chunks = indexer_service.chunk_file(path, content)
            code_chunks.extend(file_chunks)
            
        # --- STEP 3: FETCH PRs ---
        update_progress('PROGRESS', 'fetching_prs', 50)
        print(f"[{repo.owner}/{repo.repo_name}] Fetching merged pull requests...")
        pr_chunks = pr_service.fetch_and_chunk_prs(repo.owner, repo.repo_name)

        # --- STEP 4: EMBED ---
        update_progress('PROGRESS', 'embedding', 70)
        print(f"[{repo.owner}/{repo.repo_name}] Generating vector embeddings...")
        
        code_embeddings = indexer_service.embed_chunks(code_chunks, task_type="CODE_RETRIEVAL_DOCUMENT")
        pr_embeddings = indexer_service.embed_chunks(pr_chunks, task_type="RETRIEVAL_DOCUMENT")

        # --- STEP 5: STORE IN CHROMADB ---
        update_progress('PROGRESS', 'storing', 90)
        print(f"[{repo.owner}/{repo.repo_name}] Storing embeddings in ChromaDB...")
        
        # 5a. Store code chunks
        if code_chunks:
            code_ids = [f"code_{repo_id}_{i}" for i in range(len(code_chunks))]
            code_metadatas = [
                {
                    "file_path": c["file_path"],
                    "start_line": c["start_line"],
                    "end_line": c["end_line"],
                    "language": c["language"]
                }
                for c in code_chunks
            ]
            code_docs = [c["content"] for c in code_chunks]
            chroma_service.store_embeddings(
                collection_name=f"repo_{repo_id}_code",
                ids=code_ids,
                embeddings=code_embeddings,
                metadatas=code_metadatas,
                documents=code_docs
            )

        # 5b. Store PR chunks
        if pr_chunks:
            pr_ids = [f"pr_{repo_id}_{i}" for i in range(len(pr_chunks))]
            pr_metadatas = [c["metadata"] for c in pr_chunks]
            # Convert files_changed list to comma separated string as ChromaDB metadata values must be strings, integers or floats
            for meta in pr_metadatas:
                if "files_changed" in meta and isinstance(meta["files_changed"], list):
                    meta["files_changed"] = ", ".join(meta["files_changed"])
            
            pr_docs = [c["content"] for c in pr_chunks]
            chroma_service.store_embeddings(
                collection_name=f"repo_{repo_id}_prs",
                ids=pr_ids,
                embeddings=pr_embeddings,
                metadatas=pr_metadatas,
                documents=pr_docs
            )

        # --- STEP 6: DONE ---
        repo.status = "ready"
        repo.file_count = len(file_tree)
        repo.chunk_count = len(code_chunks)
        repo.pr_count = len(pr_chunks)
        repo.last_indexed_at = datetime.utcnow()
        db.session.commit()
        
        update_progress('SUCCESS', 'done', 100)
        print(f"[{repo.owner}/{repo.repo_name}] Indexing completed successfully!")
        return {"status": "SUCCESS", "files": len(file_tree), "chunks": len(code_chunks), "prs": len(pr_chunks)}

    except Exception as e:
        db.session.rollback()
        repo.status = "failed"
        db.session.commit()
        error_msg = f"Indexing failed for repo {repo_id}: {str(e)}"
        print(error_msg)
        if self.request.id:
            self.update_state(state='FAILURE', meta={'error': error_msg})
        raise e
