# Dependency Analyzer

This tool analyzes dependencies of a GitHub repository, supporting Java, Python, and JavaScript/TypeScript projects. It can output dependency information in various formats, including JSON, CSV, and CycloneDX SBOM (currently for npm ecosystem only).

## Prerequisites

- Python 3.6 or higher
- `requests` library
- `semver` library

To install the required libraries:
pip install requests semver

## Setup

1. Clone this repository:
git clone https://github.com/yourusername/dependency-analyzer.git
cd dependency-analyzer

2. Set up your GitHub token as an environment variable:
export GITHUB_TOKEN=your_token_here

## Usage

The basic command structure is:
python main.py <repository_url> [options]

### Options

- `-o, --output`: Specify the output format (default: console)
  - Choices: `console`, `json`, `csv`, `cyclonedx`
- `-v, --verbose`: Increase output verbosity
- `--internal-packages`: Specify internal package names (for Java projects)

### Examples

1. For console output (default):
python main.py https://github.com/username/repo

2. For JSON output:
python main.py https://github.com/username/repo -o json

3. For CSV output:
python main.py https://github.com/username/repo -o csv

4. For CycloneDX SBOM format (npm ecosystem only):
python main.py https://github.com/username/repo -o cyclonedx

5. In verbose mode:
python main.py https://github.com/username/repo -v

6. Specifying internal packages (for Java projects):
python main.py https://github.com/username/repo --internal-packages mycompany internalproject

## Supported Languages and Package Managers

- Java (Gradle)
- Python (requirements.txt)
- JavaScript/TypeScript (package.json)

## Features

- Detects the primary language of the repository
- Parses dependency files based on the detected language
- Retrieves license information for dependencies
- Supports various output formats (console, JSON, CSV)
- Generates CycloneDX SBOM for npm packages
- Allows specification of internal packages for Java projects

## Limitations

- CycloneDX SBOM generation is currently only supported for JavaScript/TypeScript (npm) projects
- For Java projects, only Gradle is supported (no Maven support yet)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

## TODO

Add CycloneDX SBOM support for Python and Java projects 

Add Maven build management parsing

Add Python Poetry build management parsing