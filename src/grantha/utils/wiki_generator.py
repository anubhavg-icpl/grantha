"""
Wiki structure generation with Mermaid diagram support for Grantha API.
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import os

from src.grantha.utils.data_pipeline import download_repo
from src.grantha.core.config import get_model_config
from src.grantha.utils.prompts import WIKI_GENERATION_PROMPT, MERMAID_DIAGRAM_PROMPT

logger = logging.getLogger(__name__)


class WikiGenerator:
    """Generates wiki structures with Mermaid diagrams for repositories."""

    def __init__(self, provider: str = "google", model: Optional[str] = None):
        """
        Initialize the WikiGenerator.

        Args:
            provider: LLM provider to use
            model: Specific model to use
        """
        self.provider = provider
        self.model = model
        self.model_config = get_model_config(provider, model)
        self.model_client = self.model_config["model_client"]()

    def generate_wiki_structure(self,
                               repo_path: str,
                               repo_url: str,
                               language: str = "en") -> Dict[str, Any]:
        """
        Generate a wiki structure for a repository.

        Args:
            repo_path: Local path to the repository
            repo_url: URL of the repository
            language: Language for the wiki content

        Returns:
            Dictionary containing the wiki structure
        """
        logger.info(f"Generating wiki structure for {repo_url}")

        # Analyze repository structure
        repo_structure = self._analyze_repository(repo_path)

        # Generate wiki pages based on repository analysis
        wiki_pages = self._generate_wiki_pages(repo_structure, repo_url, language)

        # Generate navigation structure
        wiki_sections = self._generate_wiki_sections(wiki_pages)

        # Create the complete wiki structure
        wiki_structure = {
            "id": f"wiki_{Path(repo_path).name}",
            "title": self._generate_wiki_title(repo_url),
            "description": self._generate_wiki_description(repo_structure, language),
            "pages": wiki_pages,
            "sections": wiki_sections,
            "rootSections": [section["id"] for section in wiki_sections[:3]],  # Top 3 sections as root
            "generated_at": datetime.now().isoformat(),
            "language": language
        }

        return wiki_structure

    def _analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        Analyze repository structure and content.

        Args:
            repo_path: Path to the repository

        Returns:
            Dictionary containing repository analysis
        """
        structure = {
            "directories": {},
            "files": {},
            "languages": {},
            "patterns": {}
        }

        # Walk through repository
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'dist', 'build', '__pycache__']]

            rel_path = os.path.relpath(root, repo_path)
            if rel_path == '.':
                rel_path = ''

            structure["directories"][rel_path] = {
                "files": files,
                "subdirs": dirs
            }

            # Analyze file types
            for file in files:
                ext = Path(file).suffix
                if ext:
                    structure["languages"][ext] = structure["languages"].get(ext, 0) + 1

        # Detect common patterns
        structure["patterns"] = self._detect_patterns(structure)

        return structure

    def _detect_patterns(self, structure: Dict[str, Any]) -> Dict[str, bool]:
        """Detect common repository patterns."""
        patterns = {
            "is_python": ".py" in structure["languages"],
            "is_javascript": ".js" in structure["languages"] or ".ts" in structure["languages"],
            "is_react": any("react" in str(d).lower() for d in structure["directories"]),
            "has_api": any("api" in str(d).lower() for d in structure["directories"]),
            "has_tests": any("test" in str(d).lower() for d in structure["directories"]),
            "has_docs": any("doc" in str(d).lower() for d in structure["directories"]),
        }
        return patterns

    def _generate_wiki_pages(self,
                            repo_structure: Dict[str, Any],
                            repo_url: str,
                            language: str) -> List[Dict[str, Any]]:
        """
        Generate wiki pages based on repository structure.

        Args:
            repo_structure: Repository analysis
            repo_url: Repository URL
            language: Language for content

        Returns:
            List of wiki pages
        """
        pages = []

        # Overview page
        pages.append({
            "id": "overview",
            "title": "Project Overview",
            "content": self._generate_overview_content(repo_structure, repo_url, language),
            "filePaths": [],
            "importance": "high",
            "relatedPages": ["architecture", "getting-started"]
        })

        # Architecture page with Mermaid diagram
        pages.append({
            "id": "architecture",
            "title": "System Architecture",
            "content": self._generate_architecture_content(repo_structure, language),
            "filePaths": [],
            "importance": "high",
            "relatedPages": ["overview", "api-reference"],
            "mermaidDiagram": self._generate_architecture_diagram(repo_structure)
        })

        # Getting Started page
        pages.append({
            "id": "getting-started",
            "title": "Getting Started",
            "content": self._generate_getting_started_content(repo_structure, language),
            "filePaths": ["README.md", "INSTALL.md", "setup.py", "package.json"],
            "importance": "high",
            "relatedPages": ["overview", "configuration"]
        })

        # API Reference if applicable
        if repo_structure["patterns"].get("has_api"):
            pages.append({
                "id": "api-reference",
                "title": "API Reference",
                "content": self._generate_api_reference_content(repo_structure, language),
                "filePaths": [],
                "importance": "medium",
                "relatedPages": ["architecture", "examples"],
                "mermaidDiagram": self._generate_api_flow_diagram(repo_structure)
            })

        # Data Flow diagram page
        pages.append({
            "id": "data-flow",
            "title": "Data Flow",
            "content": self._generate_data_flow_content(repo_structure, language),
            "filePaths": [],
            "importance": "medium",
            "relatedPages": ["architecture", "api-reference"],
            "mermaidDiagram": self._generate_data_flow_diagram(repo_structure)
        })

        # Testing documentation if tests exist
        if repo_structure["patterns"].get("has_tests"):
            pages.append({
                "id": "testing",
                "title": "Testing Guide",
                "content": self._generate_testing_content(repo_structure, language),
                "filePaths": [],
                "importance": "medium",
                "relatedPages": ["getting-started", "contributing"]
            })

        return pages

    def _generate_wiki_sections(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate navigation sections for the wiki."""
        sections = [
            {
                "id": "introduction",
                "title": "Introduction",
                "pages": ["overview", "getting-started"],
                "subsections": []
            },
            {
                "id": "technical",
                "title": "Technical Documentation",
                "pages": ["architecture", "data-flow"],
                "subsections": ["api", "testing"] if any(p["id"] in ["api-reference", "testing"] for p in pages) else []
            }
        ]

        # Add API subsection if exists
        if any(p["id"] == "api-reference" for p in pages):
            sections.append({
                "id": "api",
                "title": "API Documentation",
                "pages": ["api-reference"],
                "subsections": []
            })

        # Add testing subsection if exists
        if any(p["id"] == "testing" for p in pages):
            sections.append({
                "id": "testing",
                "title": "Testing",
                "pages": ["testing"],
                "subsections": []
            })

        return sections

    def _generate_architecture_diagram(self, repo_structure: Dict[str, Any]) -> str:
        """Generate Mermaid diagram for system architecture."""
        diagram = "graph TB\n"

        # Detect main components
        if repo_structure["patterns"].get("is_python"):
            diagram += "    Client[Client Application]\n"
            diagram += "    API[Python API Server]\n"
            diagram += "    DB[(Database)]\n"
            diagram += "    Client --> API\n"
            diagram += "    API --> DB\n"

        if repo_structure["patterns"].get("is_javascript"):
            diagram += "    Frontend[Frontend - JS/React]\n"
            diagram += "    Backend[Backend Server]\n"
            diagram += "    Frontend --> Backend\n"

        if repo_structure["patterns"].get("has_api"):
            diagram += "    APIGateway[API Gateway]\n"
            diagram += "    Services[Microservices]\n"
            diagram += "    APIGateway --> Services\n"

        return diagram

    def _generate_data_flow_diagram(self, repo_structure: Dict[str, Any]) -> str:
        """Generate Mermaid diagram for data flow."""
        diagram = "flowchart LR\n"
        diagram += "    Input[User Input]\n"
        diagram += "    Process[Data Processing]\n"
        diagram += "    Storage[(Data Storage)]\n"
        diagram += "    Output[Output/Response]\n"
        diagram += "    Input --> Process\n"
        diagram += "    Process --> Storage\n"
        diagram += "    Storage --> Process\n"
        diagram += "    Process --> Output\n"

        return diagram

    def _generate_api_flow_diagram(self, repo_structure: Dict[str, Any]) -> str:
        """Generate Mermaid sequence diagram for API flow."""
        diagram = "sequenceDiagram\n"
        diagram += "    participant Client\n"
        diagram += "    participant API\n"
        diagram += "    participant Service\n"
        diagram += "    participant Database\n\n"
        diagram += "    Client->>API: Request\n"
        diagram += "    API->>Service: Process Request\n"
        diagram += "    Service->>Database: Query Data\n"
        diagram += "    Database-->>Service: Return Data\n"
        diagram += "    Service-->>API: Process Response\n"
        diagram += "    API-->>Client: Response\n"

        return diagram

    def _generate_wiki_title(self, repo_url: str) -> str:
        """Generate wiki title from repository URL."""
        parts = repo_url.rstrip('/').split('/')
        if len(parts) >= 2:
            return f"{parts[-1]} Documentation"
        return "Project Documentation"

    def _generate_wiki_description(self, repo_structure: Dict[str, Any], language: str) -> str:
        """Generate wiki description."""
        lang_map = {
            "en": "Comprehensive documentation and technical reference",
            "zh": "综合文档和技术参考",
            "ja": "包括的なドキュメントと技術リファレンス",
            "es": "Documentación completa y referencia técnica",
            "fr": "Documentation complète et référence technique"
        }
        return lang_map.get(language, lang_map["en"])

    def _generate_overview_content(self, repo_structure: Dict[str, Any], repo_url: str, language: str) -> str:
        """Generate overview page content."""
        content = f"# Project Overview\n\n"
        content += f"Welcome to the documentation for this project.\n\n"
        content += f"## Repository\n\n"
        content += f"- **URL**: {repo_url}\n"
        content += f"- **Primary Languages**: {', '.join(repo_structure['languages'].keys())}\n\n"
        content += f"## Project Structure\n\n"
        content += f"This repository contains {len(repo_structure['directories'])} directories "
        content += f"and supports {len(repo_structure['languages'])} programming languages.\n\n"

        return content

    def _generate_architecture_content(self, repo_structure: Dict[str, Any], language: str) -> str:
        """Generate architecture page content."""
        content = "# System Architecture\n\n"
        content += "This document describes the high-level architecture of the system.\n\n"
        content += "## Components\n\n"

        if repo_structure["patterns"].get("has_api"):
            content += "- **API Layer**: Handles external requests and responses\n"
        if repo_structure["patterns"].get("is_python"):
            content += "- **Python Backend**: Core business logic implementation\n"
        if repo_structure["patterns"].get("is_javascript"):
            content += "- **JavaScript Frontend**: User interface and client-side logic\n"

        content += "\n## Architecture Diagram\n\n"
        content += "See the Mermaid diagram below for a visual representation of the system architecture.\n\n"

        return content

    def _generate_getting_started_content(self, repo_structure: Dict[str, Any], language: str) -> str:
        """Generate getting started content."""
        content = "# Getting Started\n\n"
        content += "This guide will help you set up and run the project.\n\n"
        content += "## Prerequisites\n\n"

        if repo_structure["patterns"].get("is_python"):
            content += "- Python 3.8 or higher\n"
            content += "- pip package manager\n"
        if repo_structure["patterns"].get("is_javascript"):
            content += "- Node.js 14 or higher\n"
            content += "- npm or yarn\n"

        content += "\n## Installation\n\n"
        content += "1. Clone the repository\n"
        content += "2. Install dependencies\n"
        content += "3. Configure environment variables\n"
        content += "4. Run the application\n\n"

        return content

    def _generate_api_reference_content(self, repo_structure: Dict[str, Any], language: str) -> str:
        """Generate API reference content."""
        content = "# API Reference\n\n"
        content += "This document provides detailed information about the API endpoints.\n\n"
        content += "## Base URL\n\n"
        content += "`http://localhost:8000`\n\n"
        content += "## Endpoints\n\n"
        content += "See the API flow diagram for request/response patterns.\n\n"

        return content

    def _generate_data_flow_content(self, repo_structure: Dict[str, Any], language: str) -> str:
        """Generate data flow content."""
        content = "# Data Flow\n\n"
        content += "This document describes how data flows through the system.\n\n"
        content += "## Overview\n\n"
        content += "Data enters the system through various input channels, "
        content += "is processed according to business rules, and stored or returned as output.\n\n"
        content += "## Flow Diagram\n\n"
        content += "The diagram below illustrates the data flow through the system components.\n\n"

        return content

    def _generate_testing_content(self, repo_structure: Dict[str, Any], language: str) -> str:
        """Generate testing documentation content."""
        content = "# Testing Guide\n\n"
        content += "This guide covers the testing strategy and how to run tests.\n\n"
        content += "## Test Types\n\n"
        content += "- Unit Tests\n"
        content += "- Integration Tests\n"
        content += "- End-to-End Tests\n\n"
        content += "## Running Tests\n\n"

        if repo_structure["patterns"].get("is_python"):
            content += "```bash\npytest\n```\n\n"
        if repo_structure["patterns"].get("is_javascript"):
            content += "```bash\nnpm test\n```\n\n"

        return content


# Add prompts to prompts.py
WIKI_GENERATION_PROMPT = """
Generate a comprehensive wiki structure for the following repository.
Consider the repository structure, programming languages used, and common patterns.
Create documentation that is helpful for both users and developers.

Repository Analysis:
{repo_analysis}

Language: {language}

Generate wiki pages that cover:
1. Project overview
2. Architecture and design
3. Getting started guide
4. API documentation (if applicable)
5. Testing documentation (if applicable)
"""

MERMAID_DIAGRAM_PROMPT = """
Generate a Mermaid diagram for the following component:
Component Type: {component_type}
Repository Structure: {repo_structure}

Create a clear, informative diagram that visualizes the {component_type}.
Use appropriate Mermaid syntax (graph, flowchart, or sequenceDiagram).
"""
