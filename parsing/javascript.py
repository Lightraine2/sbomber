import json
import requests
import semver
import hashlib
from uuid import uuid4
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

    def generate_cyclonedx_sbom(self, repo_info, dependencies):
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "serialNumber": f"urn:uuid:{uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": self.get_timestamp(),
                "tools": [
                    {
                        "vendor": "Your Tool Name",
                        "name": "Your Tool Name",
                        "version": "1.0.0"
                    }
                ],
                "component": {
                    "type": "application",
                    "name": repo_info['name'],
                    "version": "1.0.0"
                }
            },
            "components": []
        }

        for dep in dependencies:
            component = self.generate_component(dep)
            sbom["components"].append(component)

        return json.dumps(sbom, indent=2)

    def generate_component(self, dep):
        component = {
            "type": "library",
            "name": dep.name,
            "version": dep.version,
        }

        npm_info = self.fetch_npm_package_info(dep.name, dep.version)
        if npm_info:
            component.update(self.get_component_details(dep.name, npm_info))
        else:
            component.update({
                "purl": f"pkg:npm/{dep.name}@{dep.version}",
                "bom-ref": f"pkg:npm/{dep.name}@{dep.version}"
            })

        if dep.license:
            component["licenses"] = [{"license": {"id": dep.license}}]

        return component

    def get_component_details(self, package_name, npm_info):
        resolved_version = npm_info["version"]
        hash_content = f"{package_name}@{resolved_version}".encode('utf-8')
        sha1_hash = hashlib.sha1(hash_content).hexdigest()

        details = {
            "description": npm_info["description"],
            "version": resolved_version,
            "hashes": [{"alg": "SHA-1", "content": sha1_hash}],
            "purl": f"pkg:npm/{package_name}@{resolved_version}",
            "bom-ref": f"pkg:npm/{package_name}@{resolved_version}",
            "externalReferences": []
        }

        if npm_info["homepage"]:
            details["externalReferences"].append({"type": "website", "url": npm_info["homepage"]})
        if npm_info["bugs"]:
            details["externalReferences"].append({"type": "issue-tracker", "url": npm_info["bugs"]})
        if npm_info["repository"]:
            details["externalReferences"].append({"type": "vcs", "url": npm_info["repository"]})

        return details

    def fetch_npm_package_info(self, package_name, version_range):
        if version_range.startswith('file:'):
            print(f"Local file dependency detected for {package_name}. Skipping npm info fetch.")
            return None

        try:
            response = requests.get(self.npm_url.format(package=package_name))
            response.raise_for_status()
            data = response.json()
            
            versions = list(data['versions'].keys())
            parsed_range = self.parse_version_range(version_range)
            valid_versions = [v for v in versions if self.version_satisfies(v, parsed_range)]

            if not valid_versions:
                print(f"No valid version found for {package_name}@{version_range}")
                return None
            
            latest_valid_version = max(valid_versions, key=semver.VersionInfo.parse)
            version_data = data['versions'][latest_valid_version]
            
            return {
                "version": latest_valid_version,
                "description": version_data.get("description", ""),
                "repository": version_data.get("repository", {}).get("url", ""),
                "homepage": version_data.get("homepage", ""),
                "bugs": version_data.get("bugs", {}).get("url", "")
            }
        except requests.RequestException as e:
            print(f"Error fetching npm info for {package_name}@{version_range}: {str(e)}")
        except (KeyError, ValueError) as e:
            print(f"Error parsing npm info for {package_name}@{version_range}: {str(e)}")
        return None

    @staticmethod
    def parse_version_range(version_range):
        if version_range.startswith('^'):
            base_version = version_range[1:]
            major = int(base_version.split('.')[0])
            return f">={base_version} <{major+1}.0.0"
        elif version_range.startswith('~'):
            base_version = version_range[1:]
            major, minor = map(int, base_version.split('.')[:2])
            return f">={base_version} <{major}.{minor+1}.0"
        else:
            return version_range

    @staticmethod
    def version_satisfies(version, range_str):
        if range_str.startswith('>='):
            min_version, max_version = range_str.split()
            return semver.VersionInfo.parse(version) >= semver.VersionInfo.parse(min_version[2:]) and \
                   semver.VersionInfo.parse(version) < semver.VersionInfo.parse(max_version[1:])
        else:
            return semver.match(version, range_str)

    @staticmethod
    def get_timestamp():
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"