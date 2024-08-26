import json
from parsing.base import BaseParser
from models.dependency import Dependency

class JavaScriptParser(BaseParser):
    def get_dependency_file_name(self):
        return "package.json"

    def parse_dependencies(self, file_content):
        package_json = json.loads(file_content)
        dependencies = []

        for dep_type in ['dependencies', 'devDependencies']:
            if dep_type in package_json:
                for name, version in package_json[dep_type].items():
                    dependencies.append(Dependency(name, version, "Unknown"))

        return dependencies