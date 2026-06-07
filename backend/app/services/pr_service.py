class PRService:
    def __init__(self, github_service):
        self.gh_service = github_service

    def filter_bots(self, pr_author):
        """Filter bot/automation accounts."""
        author = pr_author.lower()
        bot_keywords = ["bot", "dependabot", "renovate"]
        return any(keyword in author for keyword in bot_keywords)

    def fetch_and_chunk_prs(self, owner, repo_name):
        """
        Fetch last 100 merged PRs and build text chunks.
        Return format: list of dicts containing chunk data and metadata.
        """
        # Stub implementation
        return []
