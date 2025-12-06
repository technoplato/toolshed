"""
HOW:
  Use to get an instance of the repository.
  `repo = DatabaseFactory.get_repository(config)`
  
  [Inputs]
  - config: A configuration object (dict or specific Config class) containing connection details.

  [Outputs]
  - An instance implementing VideoAnalysisRepository.

WHO:
  Antigravity, User
  (Context: Bootstrapping data access)

WHAT:
  Factory class that encapsulates the logic of choosing which data backend to use.
  Currently supports:
  - 'legacy_json': Uses local manifest.json
  - 'composite': Uses InstantDB + Postgres (TODO)

WHEN:
  2025-12-05

WHERE:
  apps/speaker-diarization-benchmark/src/data/factory.py

WHY:
  To allow the application to switch between "Dev Mode" (JSON files) and "Prod Mode" (Database)
  via configuration, without changing any functional code.
"""

from typing import Dict, Any
from .repository import VideoAnalysisRepository
# Import implementations lazily inside the method to avoid circular imports? 
# Or just import them here if they are in submodules.

class DatabaseFactory:
    
    @staticmethod
    def get_repository(config: Dict[str, Any]) -> VideoAnalysisRepository:
        """
        Returns a configured repository instance.
        
        Config schema expected:
        {
            "type": "json" | "composite",
            "json_options": {
                "manifest_path": "path/to/manifest.json",
                "embeddings_path": "path/to/embeddings.json"
            },
            "composite_options": {
                "instant_db_app_id": "...",
                "postgres_url": "..."
            }
        }
        """
        repo_type = config.get("type", "json")
        
        if repo_type == "json":
            from .impl.json_adapter import LegacyJsonRepository
            manifest_path = config.get("json_options", {}).get("manifest_path", "data/clips/manifest.json")
            embeddings_path = config.get("json_options", {}).get("embeddings_path", "data/speaker_embeddings.json")
            return LegacyJsonRepository(manifest_path, embeddings_path)
            
        elif repo_type == "composite":
            from .impl.composite_video_and_embedding_db_adapter import CompositeVideoAndEmbeddingDbAdapter
            return CompositeVideoAndEmbeddingDbAdapter(config.get("composite_options", {}))
            
        else:
            raise ValueError(f"Unknown repository type: {repo_type}")
