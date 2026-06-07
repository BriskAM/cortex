class PRService:
    def __init__(self, github_service):
        self.gh_service = github_service

    def filter_bots(self, pr_author):
        """Filter bot/automation accounts."""
        author = pr_author.lower()
        bot_keywords = {"bot", "dependabot", "renovate"}
        return any(keyword in author for keyword in bot_keywords)

    def _format_diff_summary(self, pr_obj):
        """Extract diff hunks for the first 5 files, capped at 200 chars each."""
        diff_parts = []
        try:
            # pr_obj is a PyGithub PullRequest object passed in metadata
            files = pr_obj.get_files()
            for idx, f in enumerate(files):
                if idx >= 5:
                    break
                patch = f.patch or ""
                truncated_patch = patch[:200]
                diff_parts.append(f"File: {f.filename}\nDiff:\n{truncated_patch}...")
        except Exception as e:
            print(f"Failed to fetch files/patch for PR diff summary: {e}")
            
        return "\n\n".join(diff_parts) if diff_parts else "No diff patch available."

    def build_pr_chunk(self, pr_data):
        """
        Builds a single text chunk representation for a merged Pull Request.
        """
        pr_obj = pr_data.get("_pr_obj")
        diff_summary = self._format_diff_summary(pr_obj) if pr_obj else "No diff patch available."
        
        files_str = ", ".join(pr_data.get("files_changed", []))
        body_truncated = pr_data.get("body", "")[:1000]
        
        chunk_text = f"""PR #{pr_data['number']}: {pr_data['title']}
Author: {pr_data['author']}
Merged: {pr_data['merged_at']}
Files changed: {files_str}

Description:
{body_truncated}

Key changes:
{diff_summary}
"""
        return {
            "content": chunk_text,
            "metadata": {
                "pr_number": pr_data["number"],
                "pr_title": pr_data["title"],
                "pr_url": pr_data["html_url"],
                "pr_author": pr_data["author"],
                "merged_at": pr_data["merged_at"],
                "files_changed": pr_data["files_changed"]
            }
        }

    def fetch_and_chunk_prs(self, owner, repo_name):
        """
        Fetches last 100 merged PRs and formats them into RAG indexing chunks.
        """
        prs_data = self.gh_service.fetch_last_100_prs(owner, repo_name)
        chunks = []
        for pr_data in prs_data:
            if self.filter_bots(pr_data["author"]):
                continue
            pr_chunk = self.build_pr_chunk(pr_data)
            chunks.append(pr_chunk)
        return chunks
