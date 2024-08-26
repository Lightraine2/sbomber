import re
from parsing.base import BaseParser
from models.dependency import Dependency

class PythonParser(BaseParser):
    def get_dependency_file_name(self):
        return "requirements.txt"

    def parse_dependencies(self, file_content):
        dependencies = []
        dep_pattern = re.compile(r'^([^=<>]+)([=<>]+)(.+)$')
        
        for line in file_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                match = dep_pattern.match(line)
                if match:
                    name, version = match.group(1).strip(), match.group(3).strip()
                    dependencies.append(Dependency(name, version, "Unknown"))
                else:
                    dependencies.append(Dependency(line, "Unknown", "Unknown"))
        
        return dependencies
