"""Project storage utility for managing processed projects and their caches."""

import json
import os
import time
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ProjectStorage:
    """Handles storage and retrieval of processed projects."""
    
    def __init__(self, storage_dir: str = "data/projects"):
        """Initialize project storage.
        
        Args:
            storage_dir: Directory to store project data
        """
        # Make sure the storage directory is absolute or relative to the current working directory
        if not os.path.isabs(storage_dir):
            # Get the base directory (project root)
            base_dir = Path(__file__).parent.parent.parent.parent
            self.storage_dir = base_dir / storage_dir
        else:
            self.storage_dir = Path(storage_dir)
        self.projects_file = self.storage_dir / "projects.json"
        self.cache_dir = self.storage_dir / "cache"
        
        # Create directories if they don't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize projects file if it doesn't exist
        if not self.projects_file.exists():
            self._write_projects_file([])
    
    def _read_projects_file(self) -> List[Dict[str, Any]]:
        """Read the projects JSON file."""
        try:
            with open(self.projects_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not read projects file: {e}")
            return []
    
    def _write_projects_file(self, projects: List[Dict[str, Any]]) -> None:
        """Write the projects JSON file."""
        try:
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump(projects, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not write projects file: {e}")
            raise
    
    def _generate_project_id(self, owner: str, repo: str, repo_type: str, language: str) -> str:
        """Generate a unique project ID."""
        return f"{owner}_{repo}_{repo_type}_{language}_{int(time.time())}"
    
    def _get_cache_filename(self, owner: str, repo: str, repo_type: str, language: str) -> str:
        """Generate cache filename for a project."""
        return f"{owner}_{repo}_{repo_type}_{language}.json"
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """Get list of all processed projects.
        
        Returns:
            List of processed project entries
        """
        projects = self._read_projects_file()
        
        # Convert to expected format for frontend compatibility
        processed_projects = []
        for project in projects:
            processed_project = {
                "id": project.get("id", ""),
                "owner": project.get("owner", ""),
                "repo": project.get("repo", ""),
                "name": f"{project.get('owner', '')}/{project.get('repo', '')}",
                "repo_type": project.get("repo_type", "github"),
                "submittedAt": project.get("submittedAt", int(time.time() * 1000)),  # Convert to milliseconds
                "language": project.get("language", "en"),
                "provider": project.get("provider", ""),
                "model": project.get("model", "")
            }
            processed_projects.append(processed_project)
        
        # Sort by submission time, newest first
        processed_projects.sort(key=lambda x: x["submittedAt"], reverse=True)
        
        return processed_projects
    
    def save_project(
        self,
        owner: str,
        repo: str,
        repo_type: str,
        language: str,
        wiki_structure: Optional[Dict[str, Any]] = None,
        generated_pages: Optional[Dict[str, Any]] = None,
        provider: str = "google",
        model: str = ""
    ) -> str:
        """Save a processed project.
        
        Args:
            owner: Repository owner
            repo: Repository name
            repo_type: Repository type (github, gitlab, etc.)
            language: Language code
            wiki_structure: Wiki structure data
            generated_pages: Generated pages data
            provider: Model provider
            model: Model name
            
        Returns:
            Project ID of saved project
        """
        projects = self._read_projects_file()
        
        # Generate unique project ID
        project_id = self._generate_project_id(owner, repo, repo_type, language)
        
        # Create project entry
        project_entry = {
            "id": project_id,
            "owner": owner,
            "repo": repo,
            "repo_type": repo_type,
            "language": language,
            "submittedAt": int(time.time() * 1000),  # Timestamp in milliseconds
            "provider": provider,
            "model": model,
            "created_at": datetime.now().isoformat(),
            "cache_file": self._get_cache_filename(owner, repo, repo_type, language)
        }
        
        # Add to projects list
        projects.append(project_entry)
        
        # Save projects file
        self._write_projects_file(projects)
        
        # Save cache data if provided
        if wiki_structure or generated_pages:
            self._save_project_cache(
                owner, repo, repo_type, language,
                wiki_structure, generated_pages, provider, model
            )
        
        logger.info(f"Saved project: {owner}/{repo} ({repo_type}, {language})")
        return project_id
    
    def _save_project_cache(
        self,
        owner: str,
        repo: str,
        repo_type: str,
        language: str,
        wiki_structure: Optional[Dict[str, Any]],
        generated_pages: Optional[Dict[str, Any]],
        provider: str,
        model: str
    ) -> None:
        """Save project cache data."""
        cache_filename = self._get_cache_filename(owner, repo, repo_type, language)
        cache_file_path = self.cache_dir / cache_filename
        
        cache_data = {
            "owner": owner,
            "repo": repo,
            "repo_type": repo_type,
            "language": language,
            "wiki_structure": wiki_structure or {},
            "generated_pages": generated_pages or {},
            "provider": provider,
            "model": model,
            "cached_at": datetime.now().isoformat()
        }
        
        try:
            with open(cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved cache for project: {owner}/{repo}")
        except Exception as e:
            logger.error(f"Failed to save cache for project {owner}/{repo}: {e}")
            raise
    
    def get_project_cache(
        self, 
        owner: str, 
        repo: str, 
        repo_type: str, 
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached data for a project.
        
        Args:
            owner: Repository owner
            repo: Repository name
            repo_type: Repository type
            language: Language code
            
        Returns:
            Cached project data or None if not found
        """
        cache_filename = self._get_cache_filename(owner, repo, repo_type, language)
        cache_file_path = self.cache_dir / cache_filename
        
        if not cache_file_path.exists():
            return None
        
        try:
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read cache for project {owner}/{repo}: {e}")
            return None
    
    def delete_project(
        self, 
        owner: str, 
        repo: str, 
        repo_type: str, 
        language: str
    ) -> bool:
        """Delete a project and its cache.
        
        Args:
            owner: Repository owner
            repo: Repository name
            repo_type: Repository type
            language: Language code
            
        Returns:
            True if project was deleted, False if not found
        """
        projects = self._read_projects_file()
        
        # Find and remove project from list
        updated_projects = []
        found = False
        
        for project in projects:
            if (project.get("owner") == owner and 
                project.get("repo") == repo and 
                project.get("repo_type") == repo_type and 
                project.get("language") == language):
                found = True
                logger.info(f"Removing project: {owner}/{repo} ({repo_type}, {language})")
                continue
            updated_projects.append(project)
        
        if not found:
            logger.warning(f"Project not found for deletion: {owner}/{repo} ({repo_type}, {language})")
            return False
        
        # Save updated projects file
        self._write_projects_file(updated_projects)
        
        # Delete cache file
        cache_filename = self._get_cache_filename(owner, repo, repo_type, language)
        cache_file_path = self.cache_dir / cache_filename
        
        if cache_file_path.exists():
            try:
                cache_file_path.unlink()
                logger.info(f"Deleted cache file: {cache_filename}")
            except Exception as e:
                logger.error(f"Failed to delete cache file {cache_filename}: {e}")
        
        return True
    
    def cleanup_old_projects(self, days_old: int = 30) -> int:
        """Clean up projects older than specified days.
        
        Args:
            days_old: Number of days to keep projects
            
        Returns:
            Number of projects cleaned up
        """
        projects = self._read_projects_file()
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        cutoff_time_ms = cutoff_time * 1000
        
        updated_projects = []
        cleaned_count = 0
        
        for project in projects:
            submitted_at = project.get("submittedAt", 0)
            if submitted_at > cutoff_time_ms:
                updated_projects.append(project)
            else:
                cleaned_count += 1
                # Delete cache file
                cache_filename = project.get("cache_file")
                if cache_filename:
                    cache_file_path = self.cache_dir / cache_filename
                    if cache_file_path.exists():
                        try:
                            cache_file_path.unlink()
                        except Exception as e:
                            logger.error(f"Failed to delete cache file {cache_filename}: {e}")
        
        if cleaned_count > 0:
            self._write_projects_file(updated_projects)
            logger.info(f"Cleaned up {cleaned_count} old projects")
        
        return cleaned_count
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Get statistics about stored projects.
        
        Returns:
            Dictionary with project statistics
        """
        projects = self._read_projects_file()
        
        # Count by repository type
        repo_type_counts = {}
        language_counts = {}
        provider_counts = {}
        
        for project in projects:
            repo_type = project.get("repo_type", "unknown")
            language = project.get("language", "unknown")
            provider = project.get("provider", "unknown")
            
            repo_type_counts[repo_type] = repo_type_counts.get(repo_type, 0) + 1
            language_counts[language] = language_counts.get(language, 0) + 1
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        return {
            "total_projects": len(projects),
            "repo_type_counts": repo_type_counts,
            "language_counts": language_counts,
            "provider_counts": provider_counts,
            "cache_directory": str(self.cache_dir),
            "projects_file": str(self.projects_file)
        }