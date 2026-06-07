import os
from github import Github

class GitHubService:
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.gh = Github(self.token) if self.token else None

    def _get_repo(self, owner, repo_name):
        if not self.gh:
            raise ValueError("GitHub client not initialized (missing token)")
        return self.gh.get_repo(f"{owner}/{repo_name}")

    def get_repo_details(self, owner, repo_name):
        """Fetch repository details from GitHub API."""
        repo = self._get_repo(owner, repo_name)
        return {
            "name": repo.name,
            "owner": repo.owner.login,
            "default_branch": repo.default_branch,
            "html_url": repo.html_url
        }

    def fetch_file_tree(self, owner, repo_name, branch="main"):
        """
        Recursively fetch files in the repository using git tree API.
        Applies filter criteria to exclude node_modules, lock files, and binaries.
        """
        repo = self._get_repo(owner, repo_name)
        try:
            # Retrieve git tree recursively
            git_ref = repo.get_branch(branch).commit.sha
            tree_root = repo.get_git_tree(git_ref, recursive=True)
        except Exception as e:
            # Fall back to default branch if 'main' or branch is not found
            git_ref = repo.get_branch(repo.default_branch).commit.sha
            tree_root = repo.get_git_tree(git_ref, recursive=True)

        keep_extensions = {
            '.py', '.js', '.ts', '.vue', '.jsx', '.tsx', 
            '.java', '.go', '.rs', '.md', '.sql'
        }
        
        exclude_paths = {
            'node_modules/', '.git/', 'dist/', 'build/', 
            '__pycache__/', 'package-lock.json', 'yarn.lock',
            'pnpm-lock.yaml', 'poetry.lock'
        }

        files_list = []
        for element in tree_root.tree:
            # We only index files (type == 'blob')
            if element.type == 'blob':
                path = element.path
                
                # Check exclusion directories and files
                should_exclude = any(ex in path for ex in exclude_paths)
                if should_exclude:
                    continue
                    
                # Check extension
                _, ext = os.path.splitext(path)
                if ext.lower() in keep_extensions:
                    files_list.append({
                        "path": path,
                        "sha": element.sha,
                        "size": element.size
                    })
                    
        return files_list

    def fetch_file_content(self, owner, repo_name, file_path, branch="main"):
        """Fetch content of a single file from the repository."""
        repo = self._get_repo(owner, repo_name)
        try:
            content_file = repo.get_contents(file_path, ref=branch)
            if isinstance(content_file, list):
                # If path returns a list, it's a directory
                return ""
            return content_file.decoded_content.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"Failed to fetch content for {file_path}: {e}")
            return ""

    def fetch_last_100_prs(self, owner, repo_name):
        """Fetch last 100 merged pull requests, skipping bot accounts."""
        repo = self._get_repo(owner, repo_name)
        
        # Get closed PRs sorted by recently updated
        pulls = repo.get_pulls(state='closed', sort='updated', direction='desc')
        
        merged_prs = []
        bot_keywords = {"bot", "dependabot", "renovate"}
        
        for pr in pulls:
            if len(merged_prs) >= 100:
                break
                
            # Only index merged PRs
            if not pr.merged:
                continue
                
            # Filter out bot users
            author = pr.user.login.lower()
            if any(kw in author for kw in bot_keywords):
                continue
                
            # Collect file changes
            files_changed = []
            try:
                # Limit files to prevent massive API overhead
                pr_files = pr.get_files()
                for idx, f in enumerate(pr_files):
                    if idx >= 50: # Cap files list
                        break
                    files_changed.append(f.filename)
            except Exception:
                pass
                
            merged_prs.append({
                "number": pr.number,
                "title": pr.title,
                "author": pr.user.login,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "body": pr.body or "",
                "html_url": pr.html_url,
                "files_changed": files_changed,
                # Store PyGithub PR object for diff scraping later
                "_pr_obj": pr
            })
            
        return merged_prs
