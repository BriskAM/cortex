import os
from google import genai
from google.genai import types
from backend.app.services.chroma_service import ChromaService
from backend.app.services.indexer_service import IndexerService
from backend.app.models.chat import Message
from backend.app.extensions import db

class RAGService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.chroma_service = ChromaService()
        self.indexer_service = IndexerService()

    def query_rag(self, repo_id, session_id, user_message, scope="repo", pr_number=None):
        """
        Retrieves relevant context from code and PR vector collections,
        combines them with history, compiles the prompt, and yields streamed response tokens.
        """
        # 1. Embed query
        # We pass task_type="CODE_RETRIEVAL_QUERY" which indexer translates to RETRIEVAL_QUERY
        query_vector = self.indexer_service.embed_chunks(
            chunks=[{"content": user_message}],
            task_type="CODE_RETRIEVAL_QUERY"
        )[0]

        # 2. Query both collections
        # 2a. Query repo_{id}_code for top 6 items
        code_results = self.chroma_service.query_embeddings(
            collection_name=f"repo_{repo_id}_code",
            query_embedding=query_vector,
            n_results=6
        )

        # 2b. Query repo_{id}_prs for top 4 items, applying PR metadata filter if scoped
        pr_filter = {"pr_number": pr_number} if scope == "pr" and pr_number is not None else None
        pr_results = self.chroma_service.query_embeddings(
            collection_name=f"repo_{repo_id}_prs",
            query_embedding=query_vector,
            n_results=4,
            filter_metadata=pr_filter
        )

        # Combine results, converting cosine distance to similarity (1.0 - distance)
        # Filter out similarity < 0.3
        retrieved_chunks = []
        
        # Parse code results
        if code_results and "documents" in code_results and code_results["documents"]:
            docs = code_results["documents"][0]
            ids = code_results["ids"][0]
            distances = code_results["distances"][0] if "distances" in code_results else [0.0] * len(docs)
            metadatas = code_results["metadatas"][0] if "metadatas" in code_results else [{}] * len(docs)
            
            for idx, doc in enumerate(docs):
                similarity = 1.0 - distances[idx]
                if similarity >= 0.3:
                    retrieved_chunks.append({
                        "type": "code",
                        "id": ids[idx],
                        "content": doc,
                        "similarity": similarity,
                        "metadata": metadatas[idx]
                    })

        # Parse PR results
        if pr_results and "documents" in pr_results and pr_results["documents"]:
            docs = pr_results["documents"][0]
            ids = pr_results["ids"][0]
            distances = pr_results["distances"][0] if "distances" in pr_results else [0.0] * len(docs)
            metadatas = pr_results["metadatas"][0] if "metadatas" in pr_results else [{}] * len(docs)
            
            for idx, doc in enumerate(docs):
                similarity = 1.0 - distances[idx]
                if similarity >= 0.3:
                    retrieved_chunks.append({
                        "type": "pr",
                        "id": ids[idx],
                        "content": doc,
                        "similarity": similarity,
                        "metadata": metadatas[idx]
                    })

        # 3. Sort by similarity descending
        retrieved_chunks.sort(key=lambda x: x["similarity"], reverse=True)

        # Deduplicate
        seen_code = set()
        seen_pr = set()
        deduped_chunks = []
        
        for chunk in retrieved_chunks:
            if chunk["type"] == "code":
                meta = chunk["metadata"]
                # Deduplicate same file + lines range
                key = (meta.get("file_path"), meta.get("start_line"), meta.get("end_line"))
                if key not in seen_code:
                    seen_code.add(key)
                    deduped_chunks.append(chunk)
            else:
                meta = chunk["metadata"]
                key = meta.get("pr_number")
                if key not in seen_pr:
                    seen_pr.add(key)
                    deduped_chunks.append(chunk)

        # Keep top 8 chunks overall
        selected_chunks = deduped_chunks[:8]

        # Map to citations JSON format
        sources = []
        for c in selected_chunks:
            if c["type"] == "code":
                meta = c["metadata"]
                sources.append({
                    "type": "code",
                    "file": meta.get("file_path"),
                    "start_line": int(meta.get("start_line", 1)),
                    "end_line": int(meta.get("end_line", 1)),
                    "snippet": c["content"],
                    "language": meta.get("language", "text")
                })
            else:
                meta = c["metadata"]
                sources.append({
                    "type": "pr",
                    "pr_number": int(meta.get("pr_number", 0)),
                    "pr_title": meta.get("pr_title", ""),
                    "pr_url": meta.get("pr_url", ""),
                    "pr_author": meta.get("pr_author", ""),
                    "merged_at": meta.get("merged_at", "")
                })

        # 4. Fetch last 3 messages from database history
        history_msgs = Message.query.filter_by(session_id=session_id).order_by(Message.created_at.desc()).limit(3).all()
        history_msgs.reverse() # Sort chronologically

        # 5. Compile prompts
        system_prompt = """You are an expert code assistant with access to both the codebase and its PR history.
Answer the user's question using the provided code snippets and PR context.
Always cite your sources — file + line numbers for code (e.g., `auth/jwt.py:42-67`), and PR number + title for history (e.g., `PR #341: feat: switch to JWT`).
If a change was introduced in a specific PR, mention it.
If you cannot answer from the context provided, say so. Do not make up answers."""

        code_context = ""
        code_blocks = [c for c in selected_chunks if c["type"] == "code"]
        for idx, c in enumerate(code_blocks):
            meta = c["metadata"]
            code_context += f"--- Code Snippet #{idx+1} ({meta.get('file_path')} Lines {meta.get('start_line')}-{meta.get('end_line')}) ---\n"
            code_context += c["content"] + "\n\n"

        pr_context = ""
        pr_blocks = [c for c in selected_chunks if c["type"] == "pr"]
        for idx, c in enumerate(pr_blocks):
            meta = c["metadata"]
            pr_context += f"--- PR History Context #{idx+1} (PR #{meta.get('pr_number')}: {meta.get('pr_title')}) ---\n"
            pr_context += c["content"] + "\n\n"

        history_context = ""
        for msg in history_msgs:
            history_context += f"{msg.role.capitalize()}: {msg.content}\n"

        user_prompt = f"""Code snippets:
{code_context if code_context else "No relevant code snippets found."}

PR history:
{pr_context if pr_context else "No relevant PR history found."}

Previous conversation:
{history_context if history_context else "None"}

Question: {user_message}"""

        # 6. LLM Stream
        model_name = os.getenv("LLM_MODEL", "gemma-4-26b-a4b-it")
        
        # Check thinking mode trigger
        thinking_keywords = ["why", "explain", "architecture", "design", "how does", "what is"]
        trigger_thinking = any(kw in user_message.lower() for kw in thinking_keywords)

        config = types.GenerateContentConfig(
            system_instruction=system_prompt
        )
        if trigger_thinking:
            try:
                # Enable thinking budget configuration
                config.thinking_config = types.ThinkingConfig(thinking_budget=2048)
            except Exception:
                pass

        if not self.client:
            # Fallback mock generator if no API client is initialized
            print("Google GenAI client not initialized (missing API key). Yielding mock response...")
            yield "Mock answer: Gemini API client not initialized. Check your GOOGLE_API_KEY.", sources
            return

        max_retries = 3
        backoff = 2
        for attempt in range(max_retries):
            try:
                response_stream = self.client.models.generate_content_stream(
                    model=model_name,
                    contents=user_prompt,
                    config=config
                )
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text, sources
                return
            except Exception as e:
                err_msg = str(e)
                print(f"Gemini LLM stream call failed (attempt {attempt+1}/{max_retries}): {err_msg}")
                
                # If thinking config is set and was likely the cause of a 400 error, disable it and retry immediately
                has_thinking = hasattr(config, 'thinking_config') and config.thinking_config is not None
                if has_thinking and ("thinking" in err_msg.lower() or "400" in err_msg or "invalid_argument" in err_msg.lower()):
                    print("Retrying generation without thinking config...")
                    config.thinking_config = None
                    continue
                
                if attempt < max_retries - 1:
                    import random
                    sleep_time = backoff + random.uniform(0, 1)
                    print(f"Transient error encountered. Waiting {sleep_time:.2f} seconds before retrying...")
                    import time
                    time.sleep(sleep_time)
                    backoff *= 2
                else:
                    yield f"Error calling LLM: {err_msg}", sources
