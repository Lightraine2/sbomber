import json
import requests
from parsing.base import BaseParser
from models.dependency import Dependency

class JavaScriptParser(BaseParser):
    def __init__(self):
        self.npm_url = "https://registry.npmjs.org/{package}"

    def get_dependency_file_name(self):
        return "package.json"

    def parse_dependencies(self, file_content):
        dependencies = []
        package_json = json.loads(file_content)

        for dep_type in ['dependencies', 'devDependencies']:
            if dep_type in package_json:
                for name, version in package_json[dep_type].items():
                    license_info = self.get_license_info(name, version)
                    dependencies.append(Dependency(name, version, license_info))

        return dependencies

    def get_license_info(self, package_name, version):
        try:
            response = requests.get(self.npm_url.format(package=package_name))
            response.raise_for_status()
            data = response.json()

            if version in data.get('versions', {}):
                specific_version = data['versions'][version]
                license_info = specific_version.get('license') or specific_version.get('licenses')
            else:
                license_info = data.get('license') or data.get('licenses')

            if isinstance(license_info, list):
                return ', '.join([lic.get('type', str(lic)) for lic in license_info])
            elif isinstance(license_info, dict):
                return license_info.get('type', str(license_info))
            elif license_info:
                return str(license_info)
            else:
                return 'Unknown'

        except requests.RequestException as e:
            print(f"Error fetching license info for {package_name}: {str(e)}")
            return "Unknown"