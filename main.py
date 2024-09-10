import sys
import os
import argparse
import json
import csv
from github import GitHubAPI
from parsing.java import JavaParser
from parsing.python import PythonParser
from parsing.javascript import JavaScriptParser

def parse_arguments():
    parser = argparse.ArgumentParser(description="Analyze dependencies of a GitHub repository")
    parser.add_argument("repo_url", help="URL of the GitHub repository to analyze")
    parser.add_argument("-o", "--output", choices=["console", "json", "csv", "cyclonedx"], default="console", help="Output format")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("--internal-packages", nargs='+', default=None, help="List of internal package names")
    return parser.parse_args()

def get_parser(language):
    if language.lower() == 'java':
        return JavaParser()
    elif language.lower() == 'python':
        return PythonParser()
    elif language.lower() == 'javascript' or language.lower() == 'typescript':
        return JavaScriptParser()
    else:
        raise ValueError(f"Unsupported language: {language}")

def main(repo_url):
    args = parse_arguments()
    
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Please set the GITHUB_TOKEN environment variable.")
        sys.exit(1)

    github_api = GitHubAPI(github_token)

    try:
        repo_info = github_api.get_repo_info(repo_url)
        language = repo_info['language']
        print(f"Detected language: {language}")

        parser = get_parser(language)
        
        if isinstance(parser, JavaParser) and args.internal_packages:
            parser.set_internal_packages(args.internal_packages)

        if isinstance(parser, JavaParser):
            gradle_file = github_api.get_dependency_file(repo_url, parser.get_dependency_file_name())
            try:
                lockfile = github_api.get_dependency_file(repo_url, parser.get_lockfile_name())
                dependencies = parser.parse_dependencies(gradle_file, lockfile)
            except Exception as e:
                if args.verbose:
                    print(f"Lockfile not found or couldn't be parsed. Falling back to gradle file only. Error: {str(e)}")
                dependencies = parser.parse_dependencies(gradle_file)
        else:
            dependency_file = github_api.get_dependency_file(repo_url, parser.get_dependency_file_name())
            dependencies = parser.parse_dependencies(dependency_file)

        if args.output == "console":
            for dep in dependencies:
                print(f"Name: {dep.name}, Version: {dep.version}, License: {dep.license}")
        elif args.output == "json":
            print(json.dumps([dep.__dict__ for dep in dependencies], indent=2))
        elif args.output == "csv":
            writer = csv.writer(sys.stdout)
            writer.writerow(["Name", "Version", "License"])
            for dep in dependencies:
                writer.writerow([dep.name, dep.version, dep.license])
        elif args.output == "cyclonedx":
            if isinstance(parser, JavaScriptParser):
                print(parser.generate_cyclonedx_sbom(repo_info, dependencies))
            else:
                print("CycloneDX SBOM generation is currently only supported for JavaScript projects.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if args.verbose:
            import traceback
            print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    args = parse_arguments()
    main(args.repo_url)