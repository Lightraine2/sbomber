import re
from parsing.base import BaseParser
from models.dependency import Dependency

class JavaParser(BaseParser):
    def get_dependency_file_name(self):
        return "build.gradle"

    def parse_dependencies(self, file_content):
        dependencies = []
        gradle_deps = self._parse_gradle_file(file_content)
        lockfile_deps = self._parse_lockfile()
        
        for dep in gradle_deps:
            version = lockfile_deps.get(dep['name'], 'Unknown')
            dependencies.append(Dependency(dep['name'], version, "Unknown"))
        
        return dependencies

    def _parse_gradle_file(self, file_content):
        deps = []
        dep_pattern = re.compile(r'(implementation|api|compileOnly|runtimeOnly)\s*[\'\"]([^:]+):([^:]+)(?::([^\'\"]*))?[\'\"]')
        
        for line in file_content.split('\n'):
            match = dep_pattern.search(line)
            if match:
                group_id, artifact_id = match.group(2), match.group(3)
                deps.append({'name': f"{group_id}:{artifact_id}"})
        
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

    def get_lockfile_name(self):
        return "gradle.lockfile"