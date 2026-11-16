import os
import json
import base64
import requests
import subprocess
from datetime import datetime

class GitHubSyncEngine:
    """
    High-performance GitHub synchronization engine for Urnav.
    Supports both direct GitHub REST API (v3) commits and native local git repositories.
    """
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config for GitHub sync: {e}")
        return {}

    def _save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def update_credentials(self, repo: str, token: str, branch: str = "main", folder: str = "summaries"):
        """Update GitHub configuration in config.json."""
        self.config["github_repo"] = repo.strip()
        self.config["github_token"] = token.strip()
        self.config["github_branch"] = branch.strip() or "main"
        self.config["github_folder"] = folder.strip() or "summaries"
        self._save_config()

    def get_repo(self) -> str:
        return self.config.get("github_repo", "")

    def get_token(self) -> str:
        return self.config.get("github_token", "")

    def get_branch(self) -> str:
        return self.config.get("github_branch", "main")

    def get_folder(self) -> str:
        return self.config.get("github_folder", "summaries")

    def push_file_to_github(self, local_file_path: str, custom_commit_msg: str = "") -> dict:
        """
        Push a file to GitHub repository.
        Returns a dictionary: {"success": bool, "message": str, "url": str}
        """
        if not os.path.exists(local_file_path):
            return {"success": False, "message": f"Local file does not exist: {local_file_path}", "url": ""}

        filename = os.path.basename(local_file_path)
        with open(local_file_path, "rb") as f:
            file_bytes = f.read()

        repo = self.get_repo()
        token = self.get_token()
        branch = self.get_branch()
        folder = self.get_folder().strip("/")

        # Check if GitHub API credentials are provided
        if repo and token:
            return self._push_via_api(repo, token, branch, folder, filename, file_bytes, custom_commit_msg)

        # Fallback: check if local directory is in a git repository
        return self._push_via_local_git(local_file_path, custom_commit_msg)

    def _push_via_api(self, repo: str, token: str, branch: str, folder: str, filename: str, file_bytes: bytes, commit_msg: str) -> dict:
        """Push directly to GitHub using the GitHub REST API v3."""
        # Sanitize repo format
        repo = repo.replace("https://github.com/", "").strip("/")
        remote_path = f"{folder}/{filename}" if folder else filename
        api_url = f"https://api.github.com/repos/{repo}/contents/{remote_path}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Urnav-Executive-Island"
        }

        # 1. Check if file already exists to obtain sha for update
        sha = None
        try:
            get_resp = requests.get(f"{api_url}?ref={branch}", headers=headers, timeout=12)
            if get_resp.status_code == 200:
                sha = get_resp.json().get("sha")
        except Exception as e:
            print(f"Notice on file check: {e}")

        # 2. Prepare PUT payload
        if not commit_msg:
            commit_msg = f"Add study summary for {filename} [via Urnav Copilot]"

        b64_content = base64.b64encode(file_bytes).decode("utf-8")
        payload = {
            "message": commit_msg,
            "content": b64_content,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha

        try:
            put_resp = requests.put(api_url, json=payload, headers=headers, timeout=20)
            if put_resp.status_code in [200, 201]:
                file_url = f"https://github.com/{repo}/blob/{branch}/{remote_path}"
                return {
                    "success": True,
                    "message": f"Successfully committed & pushed to GitHub: {repo}/{remote_path}",
                    "url": file_url
                }
            else:
                err_msg = put_resp.json().get("message", put_resp.text)
                return {
                    "success": False,
                    "message": f"GitHub API rejected commit ({put_resp.status_code}): {err_msg}",
                    "url": ""
                }
        except Exception as e:
            return {"success": False, "message": f"Network exception pushing to GitHub: {e}", "url": ""}

    def _push_via_local_git(self, local_file_path: str, commit_msg: str) -> dict:
        """Fallback push using local Git CLI if repo is a git worktree."""
        file_dir = os.path.dirname(os.path.abspath(local_file_path))
        filename = os.path.basename(local_file_path)

        # Look for .git in parent directories
        curr = file_dir
        git_root = None
        for _ in range(5):
            if os.path.exists(os.path.join(curr, ".git")):
                git_root = curr
                break
            parent = os.path.dirname(curr)
            if parent == curr:
                break
            curr = parent

        if not git_root:
            return {
                "success": False,
                "message": "GitHub credentials not configured in Urnav. Please set GitHub Repo & Personal Access Token.",
                "url": ""
            }

        if not commit_msg:
            commit_msg = f"Add study summary for {filename} [via Urnav Copilot]"

        try:
            subprocess.run(["git", "add", local_file_path], cwd=git_root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=git_root, check=True, capture_output=True)
            push_res = subprocess.run(["git", "push"], cwd=git_root, check=True, capture_output=True, text=True)
            return {
                "success": True,
                "message": f"Committed and pushed to local git remote successfully.",
                "url": ""
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Git CLI error: {e.stderr or e.stdout or str(e)}",
                "url": ""
            }
