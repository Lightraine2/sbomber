import re
import requests
import json
from functools import lru_cache
from parsing.base import BaseParser
from models.dependency import Dependency

class JavaParser(BaseParser):
    def __init__(self):
        self.gradle_file = "build.gradle"
        self.lockfile = "gradle.lockfile"
        self.maven_search_url = "https://search.maven.org/solrsearch/select"

    def get_dependency_file_name(self):
        return self.gradle_file

    def parse_dependencies(self, file_content, lockfile_content=None):
        ext_versions = self._parse_ext_block(file_content)
        if lockfile_content:
            dependencies = self._parse_with_lockfile(file_content, lockfile_content, ext_versions)
        else:
            dependencies = self._parse_without_lockfile(file_content, ext_versions)

        # Fetch license information for each dependency
        for dep in dependencies:
            dep.license = self._get_license_info(dep.name, dep.version)
            if "License not specified" in dep.license or "Not found" in dep.license:
                print(self.suggest_license_sources(dep.name))

        return dependencies

    def _parse_ext_block(self, file_content):
        ext_versions = {}
        ext_block_pattern = re.compile(r'ext\s*{([^}]*)}', re.DOTALL)
        version_pattern = re.compile(r'(\w+)Version\s*=\s*[\'"]([^\'"]+)[\'"]')

        ext_match = ext_block_pattern.search(file_content)
        if ext_match:
            ext_block = ext_match.group(1)
            for match in version_pattern.finditer(ext_block):
                name, version = match.groups()
                ext_versions[name.lower()] = version
        return ext_versions

    def _parse_with_lockfile(self, gradle_content, lockfile_content, ext_versions):
        gradle_deps = self._parse_gradle_file(gradle_content, ext_versions)
        lockfile_deps = self._parse_lockfile(lockfile_content)

        dependencies = []
        for dep in gradle_deps:
            version = lockfile_deps.get(dep.name, dep.version)
            dependencies.append(Dependency(dep.name, version, dep.license))

        return dependencies

    def _parse_without_lockfile(self, gradle_content, ext_versions):
        return self._parse_gradle_file(gradle_content, ext_versions)

    def _parse_gradle_file(self, file_content, ext_versions):
        deps = []
        dep_pattern = re.compile(r'(implementation|api|compileOnly|runtimeOnly)\s*[\'\"]([^:]+):([^:]+)(?::([^\'\"]*))?[\'\"]')

        for line in file_content.split('\n'):
            match = dep_pattern.search(line)
            if match:
                _, group_id, artifact_id, version = match.groups()
                name = f"{group_id}:{artifact_id}"

                if version:
                    if version.startswith('$'):
                        # Handle variable reference
                        var_name = version[1:].lower()  # Remove '$' and convert to lowercase
                        version = ext_versions.get(var_name, 'Unknown')
                    elif version.startswith('${') and version.endswith('}'):
                        # Handle more complex variable references like ${foo.bar}
                        var_name = version[2:-1].lower()  # Remove '${' and '}' and convert to lowercase
                        version = ext_versions.get(var_name, 'Unknown')
                else:
                    # Try to find version in ext_versions
                    var_name = artifact_id.lower()
                    version = ext_versions.get(var_name, 'Unknown')

                deps.append(Dependency(name, version, "Unknown"))

        return deps

    def _parse_lockfile(self, file_content):
        dependencies = {}
        dep_pattern = re.compile(r'^([^:]+):([^:]+):([^=]+)=(.+)$')

        for line in file_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('empty='):
                match = dep_pattern.match(line)
                if match:
                    group_id, artifact_id, version, _ = match.groups()
                    dep_name = f"{group_id}:{artifact_id}"
                    dependencies[dep_name] = version

        return dependencies

    @lru_cache(maxsize=100)
    def _get_license_info(self, dependency_name, version):
        # Check if it's a Chainalysis package
        if 'chainalysis' in dependency_name.lower():
            return 'Chainalysis'

        group_id, artifact_id = dependency_name.split(':')
        
        params = {
            'q': f'g:"{group_id}" AND a:"{artifact_id}"',
            'rows': 1,
            'wt': 'json'
        }
        
        try:
            response = requests.get(self.maven_search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['response']['docs']:
                doc = data['response']['docs'][0]
                
                # Log the entire object found in the Maven repo
                print(f"Maven Central data for {dependency_name}:")
                print(json.dumps(doc, indent=2))
                
                # Extract license information
                license = doc.get('license', [])
                if license:
                    return ', '.join(license)
                else:
                    return 'License not specified in Maven Central'
            else:
                print(f"No data found in Maven Central for {dependency_name}")
                return 'Not found in Maven Central'
        except requests.RequestException as e:
            print(f"Error fetching info for {dependency_name}: {str(e)}")
            return 'Error fetching information'

    def suggest_license_sources(self, dependency_name):
        group_id, artifact_id = dependency_name.split(':')
        maven_url = f"https://search.maven.org/artifact/{group_id}/{artifact_id}"
        github_url = f"https://github.com/search?q={group_id}+{artifact_id}"
        
        return f"License information not found in Maven Central. " \
               f"You may want to check the following sources:\n" \
               f"1. Maven Central Repository: {maven_url}\n" \
               f"2. Project's GitHub repository (if available): {github_url}\n" \
               f"3. Project's official website or documentation."

    def get_lockfile_name(self):
        return self.lockfile