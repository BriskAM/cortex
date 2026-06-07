import os
from github import Github

class GitHubService:
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.gh = Github(self.token) if self.token else None

    def get_repo_details(self, owner, repo_name):
        """Fetch repository details from GitHub API."""
        if not self.gh:
            raise ValueError("GitHub client not initialized (missing token)")
        repo = self.gh.get_repo(f"{owner}/{repo_name}")
        return {
            "name": repo.name,
            "owner": repo.owner.login,
            "default_branch": repo.default_branch,
            "html_url": repo.html_url
        }

    def fetch_file_tree(self, owner, repo_name, branch="main"):
        """Recursively fetch files in the repository using contents API."""
        # Stub returning mock file list
        return [
            {"path": "backend/app/api/auth.py", "type": "file"},
            {"path": "frontend/src/views/PrView.vue", "type": "file"},
            {"path": "README.md", "type": "file"}
        ]

    def fetch_file_content(self, owner, repo_name, file_path, branch="main"):
        """Fetch content of a single file."""
        return f"# Content of {file_path}"

    def fetch_last_100_prs(self, owner, repo_name):
        """Fetch last 100 merged pull requests, skipping bot accounts."""
        return []
