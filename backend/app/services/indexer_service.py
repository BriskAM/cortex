import os
import re
from google import genai
from google.genai import types
from tree_sitter_languages import get_parser

class IndexerService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def _get_ts_language(self, ext):
        """Map file extensions to tree-sitter language identifiers."""
        mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
        }
        return mapping.get(ext.lower())

    def _chunk_ast(self, content, ext, file_path):
        """Chunk code by function and class definitions using tree-sitter."""
        lang_id = self._get_ts_language(ext)
        if not lang_id:
            return []
            
        try:
            parser = get_parser(lang_id)
            tree = parser.parse(content.encode('utf-8'))
        except Exception as e:
            print(f"Failed to get parser for {lang_id}: {e}")
            return []

        # Nodes that signify discrete code blocks we want to index
        target_types = {
            'function_definition', 'class_definition', # Python
            'function_declaration', 'class_declaration', 'method_definition', # JS/TS
            'function_decl', 'method_decl', # Go
            'function', 'struct_item', 'impl_item' # Rust
        }

        chunks = []
        lines = content.splitlines()

        def traverse(node):
            if node.type in target_types:
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                snippet = "\n".join(lines[node.start_point[0] : node.end_point[0] + 1])
                
                # Filter out extremely small fragments
                if len(snippet.strip()) > 40:
                    chunks.append({
                        "content": snippet,
                        "file_path": file_path,
                        "start_line": start_line,
                        "end_line": end_line,
                        "language": lang_id
                    })
            for child in node.children:
                traverse(child)

        traverse(tree.root_node)
        return chunks

    def _chunk_sliding_window(self, content, file_path, window_lines=30, overlap_lines=5):
        """Fallback line-based sliding window chunker for non-AST files."""
        lines = content.splitlines()
        chunks = []
        
        # If the file is very short, keep it as a single chunk
        if len(lines) <= window_lines:
            return [{
                "content": content,
                "file_path": file_path,
                "start_line": 1,
                "end_line": max(1, len(lines)),
                "language": "text"
            }]

        start = 0
        while start < len(lines):
            end = min(start + window_lines, len(lines))
            snippet = "\n".join(lines[start:end])
            
            if len(snippet.strip()) > 20:
                chunks.append({
                    "content": snippet,
                    "file_path": file_path,
                    "start_line": start + 1,
                    "end_line": end,
                    "language": "text"
                })
                
            start += (window_lines - overlap_lines)
            
        return chunks

    def chunk_file(self, file_path, content, language=None):
        """
        Main entry point for file chunking.
        Attempts AST-aware chunking first, and falls back to sliding windows.
        """
        if not content or not content.strip():
            return []
            
        _, ext = os.path.splitext(file_path)
        
        # 1. Try tree-sitter AST chunking
        chunks = self._chunk_ast(content, ext, file_path)
        
        # 2. Fall back to sliding windows if AST parsing yielded no chunks
        if not chunks:
            chunks = self._chunk_sliding_window(content, file_path)
            
        return chunks

    def embed_chunks(self, chunks, task_type="CODE_RETRIEVAL_DOCUMENT"):
        """
        Batch generate embeddings using Google GenAI SDK.
        Returns a list of 1536-dimensional float vectors.
        """
        if not self.client:
            print("Google GenAI client not initialized (missing API key)")
            return [[0.0] * 1536 for _ in chunks]

        if not chunks:
            return []

        texts = [c["content"] for c in chunks]
        embeddings = []
        
        # Batch requests 20 items at a time
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                config = types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=1536
                )
                response = self.client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=batch,
                    config=config
                )
                for emb in response.embeddings:
                    embeddings.append(emb.values)
            except Exception as e:
                print(f"Embedding API call failed for batch starting at {i}: {e}")
                # Fallback vectors
                embeddings.extend([[0.0] * 1536 for _ in batch])
                
        return embeddings
