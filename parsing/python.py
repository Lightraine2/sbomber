import re
import requests
from parsing.base import BaseParser
from models.dependency import Dependency

class PythonParser(BaseParser):
    def __init__(self):
        self.pypi_url = "https://pypi.org/pypi/{package}/json"

    def get_dependency_file_name(self):
        return "requirements.txt"

    def parse_dependencies(self, file_content):
        dependencies = []
        dep_pattern = re.compile(r'^([^=<>]+)([=<>]+)?(.+)?$')
        
        for line in file_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                match = dep_pattern.match(line)
                if match:
                    name = match.group(1).strip()
                    version = match.group(3).strip() if match.group(3) else "Latest"
                    license_info = self.get_license_info(name)
                    dependencies.append(Dependency(name, version, license_info))
                else:
                    # Log or handle unparseable line
                    print(f"Warning: Could not parse line: {line}")
        
        return dependencies

    def get_license_info(self, package_name):
        try:
            response = requests.get(self.pypi_url.format(package=package_name))
            response.raise_for_status()
            data = response.json()
            return data['info'].get('license', 'Unknown')
        except requests.RequestException as e:
            print(f"Error fetching license info for {package_name}: {str(e)}")
            return "Unknown"

