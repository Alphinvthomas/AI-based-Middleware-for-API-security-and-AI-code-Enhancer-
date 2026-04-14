"""
GitHub Integration Module
Fetches and manages code from GitHub repositories
"""
import os
import base64
import requests
from typing import Optional, Dict, List, Tuple
from pathlib import Path

# Load environment variables from root .env file FIRST
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig removes BOM
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip().replace('\ufeff', '')  # Remove any BOM characters
                value = value.strip()
                if key:
                    os.environ[key] = value

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"


class GitHubIntegration:
    """Handle GitHub repository interactions"""
    
    def __init__(self, repo_owner: str, repo_name: str):
        """
        Initialize GitHub integration
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.repo_full_name = f"{repo_owner}/{repo_name}"
        self.headers = self._get_headers()
    
    def _get_headers(self) -> Dict:
        """Get GitHub API headers with authentication"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Security-Middleware"
        }
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        return headers
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Get file content from GitHub
        
        Args:
            file_path: Path to file in repository relative to root
            
        Returns:
            File content as string or None if failed
        """
        try:
            url = f"{GITHUB_API_BASE}/repos/{self.repo_full_name}/contents/{file_path}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Debug: show response status and first 200 chars
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # GitHub returns content as base64 encoded
                    if "content" in data:
                        content = data.get("content", "").strip()
                        if data.get("encoding") == "base64" and content:
                            try:
                                return base64.b64decode(content).decode("utf-8")
                            except Exception as decode_err:
                                print(f"Error decoding {file_path}: {decode_err}")
                                return None
                        else:
                            return content
                    else:
                        return None
                except Exception as json_err:
                    print(f"JSON error for {file_path}: {json_err}")
                    print(f"Response text: {response.text[:200]}")
                    return None
            else:
                print(f"Unexpected status code for {file_path}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching {file_path} from GitHub: {e}")
            return None
    
    def get_directory_contents(self, path: str = "") -> List[Dict]:
        """
        Get directory contents from GitHub
        
        Args:
            path: Directory path in repository
            
        Returns:
            List of files and directories with metadata
        """
        try:
            url = f"{GITHUB_API_BASE}/repos/{self.repo_full_name}/contents/{path}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            contents = response.json()
            if not isinstance(contents, list):
                return []
            
            return contents
        except Exception as e:
            print(f"Error fetching directory {path} from GitHub: {e}")
            return []
    
    def get_all_python_files(self, directory: str = "") -> List[str]:
        """
        Recursively get all Python files in a directory
        
        Args:
            directory: Directory path to search
            
        Returns:
            List of Python file paths
        """
        python_files = []
        
        def traverse(path: str):
            try:
                contents = self.get_directory_contents(path)
                for item in contents:
                    if item["type"] == "file" and item["name"].endswith(".py"):
                        python_files.append(item["path"])
                    elif item["type"] == "dir" and not item["name"].startswith("."):
                        # Avoid common directories
                        if item["name"] not in ["__pycache__", ".git", "node_modules", ".env"]:
                            traverse(item["path"])
            except Exception as e:
                print(f"Error traversing {path}: {e}")
        
        traverse(directory)
        return python_files
    
    def get_all_code_files(self, directory: str = "") -> List[str]:
        """
        Recursively get all code files in a directory (all supported languages)
        
        Args:
            directory: Directory path to search
            
        Returns:
            List of code file paths
        """
        supported_extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".cs", ".php", ".rb", ".rs", ".kt"]
        code_files = []
        
        def traverse(path: str):
            try:
                contents = self.get_directory_contents(path)
                for item in contents:
                    if item["type"] == "file":
                        # Check if file has a supported extension
                        if any(item["name"].lower().endswith(ext) for ext in supported_extensions):
                            code_files.append(item["path"])
                    elif item["type"] == "dir" and not item["name"].startswith("."):
                        # Avoid common directories
                        excluded = ["__pycache__", ".git", "node_modules", ".env", ".venv", "venv", 
                                   "env", "dist", "build", ".gradle", ".maven", "target", ".idea"]
                        if item["name"] not in excluded:
                            traverse(item["path"])
            except Exception as e:
                print(f"Error traversing {path}: {e}")
        
        traverse(directory)
        return code_files
    
    def get_repository_structure(self) -> Dict:
        """
        Get repository structure and key information
        
        Returns:
            Repository metadata
        """
        try:
            url = f"{GITHUB_API_BASE}/repos/{self.repo_full_name}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return {
                "name": data.get("name"),
                "description": data.get("description"),
                "url": data.get("html_url"),
                "language": data.get("language"),
                "topics": data.get("topics", []),
                "clone_url": data.get("clone_url"),
            }
        except Exception as e:
            print(f"Error getting repository structure: {e}")
            return {}
    
    def save_file_locally(self, file_path: str, local_path: str) -> bool:
        """
        Download file from GitHub and save locally
        
        Args:
            file_path: GitHub file path
            local_path: Local file path
            
        Returns:
            True if successful
        """
        try:
            content = self.get_file_content(file_path)
            if content is None:
                return False
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving file locally: {e}")
            return False
