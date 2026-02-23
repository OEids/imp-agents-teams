"""
ConfigLoader - Schema-Driven Configuration System

Centralizes configuration loading from YAML files with hot-reload support.
Replaces hardcoded mappings throughout the codebase with externalized configs.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import yaml

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class ConfigFileHandler(FileSystemEventHandler):
    """Handler for file change events to support hot-reload."""

    def __init__(self, loader: 'ConfigLoader'):
        self.loader = loader
        self._last_reload: Dict[str, float] = {}

    def on_modified(self, event):
        if event.src_path.endswith(('.yaml', '.yml')):
            # Debounce: ignore if modified within last second
            current_time = datetime.now().timestamp()
            last_time = self._last_reload.get(event.src_path, 0)
            if current_time - last_time > 1:
                self._last_reload[event.src_path] = current_time
                self.loader._reload_file(Path(event.src_path))


@dataclass
class ConfigCache:
    """Cached configuration data."""
    data: Dict[str, Any] = field(default_factory=dict)
    last_loaded: Dict[str, float] = field(default_factory=dict)
    file_hashes: Dict[str, str] = field(default_factory=dict)


class ConfigLoader:
    """
    Central configuration loader for schema-driven processing.

    Provides:
    - Loading YAML configs from structured directories
    - Hot-reload support when files change
    - Typed accessors for common configuration types
    - Fallback to defaults when configs missing
    """

    def __init__(self, config_dir: Optional[Path] = None, hot_reload: bool = False):
        """
        Initialize the ConfigLoader.

        Args:
            config_dir: Base configuration directory (defaults to project's config/)
            hot_reload: Enable hot-reload on file changes
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"
        self.config_dir = Path(config_dir)
        self.hot_reload = hot_reload

        self._cache = ConfigCache()
        self._observer: Optional[Any] = None
        self._loaded_files: Set[str] = set()

        # Load all configs on init
        self._load_all_configs()

        # Start hot-reload if enabled
        if hot_reload and WATCHDOG_AVAILABLE:
            self._start_watching()

    def _load_all_configs(self):
        """Load all configuration files."""
        if not self.config_dir.exists():
            return

        # Load from schemas directory
        schemas_dir = self.config_dir / "schemas"
        if schemas_dir.exists():
            for yaml_file in schemas_dir.rglob("*.yaml"):
                self._load_file(yaml_file)
            for yml_file in schemas_dir.rglob("*.yml"):
                self._load_file(yml_file)

        # Load from rules directory
        rules_dir = self.config_dir / "rules"
        if rules_dir.exists():
            for yaml_file in rules_dir.rglob("*.yaml"):
                self._load_file(yaml_file)
            for yml_file in rules_dir.rglob("*.yml"):
                self._load_file(yml_file)

    def _load_file(self, file_path: Path):
        """Load a single YAML file into cache."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                return

            # Create cache key from relative path
            try:
                rel_path = file_path.relative_to(self.config_dir)
                cache_key = str(rel_path).replace('\\', '/')
            except ValueError:
                cache_key = file_path.stem

            self._cache.data[cache_key] = data
            self._cache.last_loaded[cache_key] = os.path.getmtime(file_path)
            self._loaded_files.add(str(file_path))

        except Exception as e:
            print(f"[ConfigLoader] Error loading {file_path}: {e}")

    def _reload_file(self, file_path: Path):
        """Reload a single file after modification."""
        self._load_file(file_path)
        print(f"[ConfigLoader] Hot-reloaded {file_path.name}")

    def _start_watching(self):
        """Start watching for file changes."""
        if self._observer is not None or not WATCHDOG_AVAILABLE:
            return

        self._observer = Observer()
        handler = ConfigFileHandler(self)
        self._observer.schedule(handler, str(self.config_dir), recursive=True)
        self._observer.start()

    def stop_watching(self):
        """Stop watching for file changes."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def reload(self):
        """Force reload all configuration files."""
        self._cache = ConfigCache()
        self._loaded_files.clear()
        self._load_all_configs()

    # =========================================================================
    # Generic Accessors
    # =========================================================================

    def load_schema(self, strand: str, schema_type: str) -> Dict:
        """
        Load a schema file for a specific strand.

        Args:
            strand: Strand ID (S1, S2, S3)
            schema_type: Type of schema (sheet_mappings, pay_scales, etc.)

        Returns:
            Schema data as dictionary, empty dict if not found
        """
        cache_key = f"schemas/{strand.lower()}/{schema_type}.yaml"
        return self._cache.data.get(cache_key, {})

    def get_config(self, path: str, default: Any = None) -> Any:
        """
        Get configuration by path.

        Args:
            path: Path to config (e.g., "schemas/s2/sheet_mappings.yaml")
            default: Default value if not found

        Returns:
            Configuration data
        """
        return self._cache.data.get(path, default)

    # =========================================================================
    # S2-Specific Accessors
    # =========================================================================

    def get_sheet_mappings(self, strand: str = "S2") -> Dict[str, str]:
        """
        Get sheet name mappings for a strand.

        Maps internal sheet names to official template sheet names.

        Returns:
            Dict mapping internal name -> official name
        """
        schema = self.load_schema(strand, "sheet_mappings")
        return schema.get("mappings", {})

    def get_import_file_mappings(self, strand: str = "S2") -> Dict[str, str]:
        """
        Get import file pattern to data type mappings.

        Returns:
            Dict mapping file pattern -> data type
        """
        schema = self.load_schema(strand, "import_file_mappings")
        return schema.get("mappings", {})

    def get_staff_role_groups(self) -> Dict[str, Dict]:
        """
        Get staff role group definitions with finance codes.

        Returns:
            Dict of role group code -> role group config
        """
        schema = self.load_schema("S2", "staff_role_groups")
        return schema.get("role_groups", {})

    def get_pay_scales(self) -> Dict[str, Dict]:
        """
        Get pay scale definitions.

        Returns:
            Dict of pay scale code -> pay scale config
        """
        schema = self.load_schema("S2", "pay_scales")
        return schema.get("pay_scales", {})

    def get_combined_columns(self) -> List[str]:
        """
        Get list of columns that use combined "CODE: Title" format.

        Returns:
            List of column names requiring parsing
        """
        schema = self.load_schema("S2", "combined_columns")
        return schema.get("columns", [])

    def get_validation_rules(self, strand: str = "S2") -> Dict[str, Dict]:
        """
        Get validation rules for a strand.

        Returns:
            Dict of field name -> validation config
        """
        schema = self.load_schema(strand, "validation_rules")
        return schema.get("rules", {})

    def get_equated_week_patterns(self) -> Dict[str, Dict]:
        """
        Get equated week pattern definitions.

        Returns:
            Dict of pattern code -> pattern config
        """
        schema = self.load_schema("S2", "equated_week_patterns")
        return schema.get("patterns", {})

    def get_pension_schemes(self) -> Dict[str, Dict]:
        """
        Get pension scheme definitions.

        Returns:
            Dict of pension code -> pension config
        """
        schema = self.load_schema("S2", "pension_schemes")
        return schema.get("schemes", {})

    def get_contract_types(self) -> Dict[str, Dict]:
        """
        Get contract type definitions.

        Returns:
            Dict of contract type code -> contract type config
        """
        schema = self.load_schema("S2", "contract_types")
        return schema.get("types", {})

    def get_allowance_types(self) -> Dict[str, Dict]:
        """
        Get allowance type definitions.

        Returns:
            Dict of allowance code -> allowance config
        """
        schema = self.load_schema("S2", "allowance_types")
        return schema.get("types", {})

    # =========================================================================
    # Abbreviations (for fuzzy matching)
    # =========================================================================

    def get_abbreviations(self) -> Dict[str, List[str]]:
        """
        Get abbreviation dictionary for fuzzy matching.

        Returns:
            Dict of abbreviation -> list of expansions
        """
        cache_key = "rules/abbreviations.yaml"
        data = self._cache.data.get(cache_key, {})
        return data.get("abbreviations", {})

    # =========================================================================
    # S1-Specific Accessors
    # =========================================================================

    def get_finance_code_patterns(self) -> Dict[str, Dict]:
        """
        Get finance code pattern definitions.

        Returns:
            Dict of category -> pattern config
        """
        schema = self.load_schema("S1", "finance_codes")
        return schema.get("patterns", {})

    def get_school_types(self) -> Dict[str, str]:
        """
        Get school type definitions.

        Returns:
            Dict of school type code -> description
        """
        schema = self.load_schema("S1", "school_types")
        return schema.get("types", {})

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_stats(self) -> Dict:
        """Get statistics about loaded configs."""
        return {
            "files_loaded": len(self._loaded_files),
            "cache_keys": list(self._cache.data.keys()),
            "hot_reload_enabled": self.hot_reload and WATCHDOG_AVAILABLE,
            "config_dir": str(self.config_dir)
        }

    def validate_config(self) -> List[str]:
        """
        Validate loaded configurations.

        Returns:
            List of validation errors/warnings
        """
        errors = []

        # Check for required S2 configs
        required_s2 = [
            "sheet_mappings", "import_file_mappings", "staff_role_groups",
            "pay_scales", "combined_columns", "validation_rules"
        ]

        for config_name in required_s2:
            cache_key = f"schemas/s2/{config_name}.yaml"
            if cache_key not in self._cache.data:
                errors.append(f"Missing required S2 config: {config_name}.yaml")

        # Check abbreviations
        if "rules/abbreviations.yaml" not in self._cache.data:
            errors.append("Missing abbreviations.yaml for fuzzy matching")

        return errors


# Singleton instance for global access
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_dir: Optional[Path] = None, hot_reload: bool = False) -> ConfigLoader:
    """
    Get or create the global ConfigLoader instance.

    Args:
        config_dir: Configuration directory path
        hot_reload: Enable hot-reload

    Returns:
        ConfigLoader singleton instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_dir, hot_reload)
    return _config_loader


def reset_config_loader():
    """Reset the global ConfigLoader instance."""
    global _config_loader
    if _config_loader is not None:
        _config_loader.stop_watching()
        _config_loader = None
