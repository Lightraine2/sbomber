import requests
import base64

class GitHubAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_repo_info(self, repo_url):
        owner, repo = repo_url.split('/')[-2:]
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    # this could be better - need to search for the file and pick a result instead of looking for something in the project root. How to habdle multiple results? 
    def get_dependency_file(self, repo_url, file_name):
        owner, repo = repo_url.split('/')[-2:]
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_name}"
        print('searching for ' + url)
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        content = response.json()['content']
        return base64.b64decode(content).decode('utf-8')