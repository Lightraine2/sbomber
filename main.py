import sys
import os
from github import GitHubAPI
from parsing.java import JavaParser
from parsing.python import PythonParser
from parsing.javascript import JavaScriptParser

def main(repo_url):
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Please set the GITHUB_TOKEN environment variable.")
        sys.exit(1)

    github_api = GitHubAPI(github_token)
    repo_info = github_api.get_repo_info(repo_url)

    if repo_info['language'].lower() == 'java':
        parser = JavaParser()
    elif repo_info['language'].lower() == 'python':
        parser = PythonParser()
    elif repo_info['language'].lower() == 'javascript' or repo_info['language'].lower() == 'typescript':
        parser = JavaScriptParser()
    else:
        print(f"Unsupported language: {repo_info['language']}")
        sys.exit(1)

    dependency_file = github_api.get_dependency_file(repo_url, parser.get_dependency_file_name())
    dependencies = parser.parse_dependencies(dependency_file)

    for dep in dependencies:
        print(f"Name: {dep.name}, Version: {dep.version}, License: {dep.license}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <github_repo_url>")
        sys.exit(1)
    main(sys.argv[1])


