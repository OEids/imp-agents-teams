"""
Schema Registry - Dynamic Schema Definitions

Manages schemas for strands, teams, and columns loaded from YAML.
Replaces hardcoded TEAMS dict and column definitions.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import yaml


@dataclass
class ColumnSchema:
    """Schema for a single column."""
    name: str
    standard_name: str  # Normalized name
    data_type: str  # string, integer, decimal, date, boolean
    required: bool = False
    variations: List[str] = field(default_factory=list)  # Aliases
    format_pattern: Optional[str] = None  # Regex for validation
    format_hint: Optional[str] = None  # Human-readable format hint
    default_value: Optional[Any] = None
    valid_values: Optional[List[Any]] = None  # Enum-like constraints
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> 'ColumnSchema':
        """Create from dictionary."""
        return cls(
            name=data.get('name', ''),
            standard_name=data.get('standard_name', data.get('name', '')),
            data_type=data.get('data_type', 'string'),
            required=data.get('required', False),
            variations=data.get('variations', []),
            format_pattern=data.get('format_pattern'),
            format_hint=data.get('format_hint'),
            default_value=data.get('default_value'),
            valid_values=data.get('valid_values'),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            description=data.get('description')
        )

    def matches(self, column_name: str) -> bool:
        """Check if a column name matches this schema."""
        col_lower = column_name.lower().strip()

        # Check exact match
        if col_lower == self.name.lower():
            return True
        if col_lower == self.standard_name.lower():
            return True

        # Check variations
        for variation in self.variations:
            if col_lower == variation.lower():
                return True

        return False

    def get_all_names(self) -> Set[str]:
        """Get all possible names (for matching)."""
        names = {self.name.lower(), self.standard_name.lower()}
        names.update(v.lower() for v in self.variations)
        return names


@dataclass
class DataTypeSchema:
    """Schema for a data type within a strand."""
    name: str
    description: str
    columns: List[ColumnSchema]
    key_columns: List[str] = field(default_factory=list)  # Primary key columns
    parent_type: Optional[str] = None  # For hierarchical types

    @classmethod
    def from_dict(cls, data: Dict) -> 'DataTypeSchema':
        """Create from dictionary."""
        columns = [
            ColumnSchema.from_dict(col) if isinstance(col, dict) else col
            for col in data.get('columns', [])
        ]

        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            columns=columns,
            key_columns=data.get('key_columns', []),
            parent_type=data.get('parent_type')
        )

    def get_column(self, name: str) -> Optional[ColumnSchema]:
        """Get a column schema by name."""
        for col in self.columns:
            if col.matches(name):
                return col
        return None

    def get_required_columns(self) -> List[ColumnSchema]:
        """Get all required columns."""
        return [col for col in self.columns if col.required]


@dataclass
class StrandSchema:
    """Schema for a strand (S1, S2, S3)."""
    id: str
    name: str
    focus: str
    description: str
    indicators: List[str]  # Keywords that indicate this strand
    indicator_weight: float = 1.0  # Weight for strand detection
    data_types: List[DataTypeSchema] = field(default_factory=list)
    key_sheets: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    common_issues: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> 'StrandSchema':
        """Create from dictionary."""
        data_types = [
            DataTypeSchema.from_dict(dt) if isinstance(dt, dict) else dt
            for dt in data.get('data_types', [])
        ]

        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            focus=data.get('focus', ''),
            description=data.get('description', ''),
            indicators=data.get('indicators', []),
            indicator_weight=float(data.get('indicator_weight', 1.0)),
            data_types=data_types,
            key_sheets=data.get('key_sheets', []),
            validation_rules=data.get('validation_rules', []),
            common_issues=data.get('common_issues', [])
        )

    def get_data_type(self, name: str) -> Optional[DataTypeSchema]:
        """Get a data type schema by name."""
        name_lower = name.lower()
        for dt in self.data_types:
            if dt.name.lower() == name_lower:
                return dt
        return None

    def get_all_columns(self) -> List[ColumnSchema]:
        """Get all columns across all data types."""
        columns = []
        for dt in self.data_types:
            columns.extend(dt.columns)
        return columns

    def find_column_schema(self, column_name: str) -> Optional[ColumnSchema]:
        """Find a column schema across all data types."""
        for dt in self.data_types:
            col = dt.get_column(column_name)
            if col:
                return col
        return None


class SchemaRegistry:
    """
    Central registry for all schemas.

    Replaces hardcoded TEAMS dict and provides dynamic
    schema definitions loaded from YAML.
    """

    def __init__(self, schemas_dir: Optional[Path] = None):
        self.schemas_dir = schemas_dir or Path(__file__).parent.parent / "config" / "schemas"
        self.strands: Dict[str, StrandSchema] = {}
        self.column_mappings: Dict[str, ColumnSchema] = {}  # Global column registry

        self._load_all_schemas()

    def _load_all_schemas(self):
        """Load all schemas from YAML files."""
        if not self.schemas_dir.exists():
            return

        # Load strand schemas
        strands_file = self.schemas_dir / "strands.yaml"
        if strands_file.exists():
            self._load_strands_file(strands_file)

        # Load column mappings
        columns_file = self.schemas_dir / "columns.yaml"
        if columns_file.exists():
            self._load_columns_file(columns_file)

    def _load_strands_file(self, file_path: Path):
        """Load strand schemas from a YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                return

            strands_data = data.get('strands', [])
            for strand_data in strands_data:
                strand = StrandSchema.from_dict(strand_data)
                self.strands[strand.id] = strand

        except Exception as e:
            print(f"Error loading strands from {file_path}: {e}")

    def _load_columns_file(self, file_path: Path):
        """Load global column mappings from a YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                return

            columns_data = data.get('columns', [])
            for col_data in columns_data:
                col = ColumnSchema.from_dict(col_data)
                self.column_mappings[col.standard_name.lower()] = col

        except Exception as e:
            print(f"Error loading columns from {file_path}: {e}")

    def get_strand(self, strand_id: str) -> Optional[StrandSchema]:
        """Get a strand schema by ID."""
        return self.strands.get(strand_id.upper())

    def get_all_strands(self) -> List[StrandSchema]:
        """Get all strand schemas."""
        return list(self.strands.values())

    def get_strand_ids(self) -> List[str]:
        """Get all strand IDs."""
        return list(self.strands.keys())

    def find_column_mapping(self, column_name: str) -> Optional[ColumnSchema]:
        """Find a global column mapping."""
        col_lower = column_name.lower().strip()

        # Check exact match
        if col_lower in self.column_mappings:
            return self.column_mappings[col_lower]

        # Check variations
        for col in self.column_mappings.values():
            if col.matches(column_name):
                return col

        return None

    def find_column_in_strand(
        self,
        column_name: str,
        strand_id: str
    ) -> Optional[ColumnSchema]:
        """Find a column schema in a specific strand."""
        strand = self.get_strand(strand_id)
        if strand:
            return strand.find_column_schema(column_name)
        return None

    def detect_strand_by_indicators(self, columns: List[str]) -> List[tuple]:
        """
        Detect strand by matching column names against indicators.

        Returns list of (strand_id, score, matched_indicators) tuples,
        sorted by score descending.
        """
        results = []
        columns_lower = [c.lower() for c in columns]

        for strand_id, strand in self.strands.items():
            matched = []
            for indicator in strand.indicators:
                indicator_lower = indicator.lower()
                for col in columns_lower:
                    if indicator_lower in col:
                        matched.append(indicator)
                        break

            if matched:
                score = len(matched) * strand.indicator_weight
                results.append((strand_id, score, matched))

        # Sort by score descending
        results.sort(key=lambda x: -x[1])
        return results

    def to_teams_dict(self) -> Dict:
        """
        Convert to legacy TEAMS dict format for backward compatibility.

        Allows gradual migration from hardcoded TEAMS.
        """
        teams = {}
        for strand_id, strand in self.strands.items():
            teams[strand_id] = {
                "name": strand.name,
                "focus": strand.focus,
                "description": strand.description,
                "key_sheets": strand.key_sheets,
                "indicators": strand.indicators
            }
        return teams

    def register_strand(self, strand: StrandSchema):
        """Register a strand schema programmatically."""
        self.strands[strand.id] = strand

    def register_column(self, column: ColumnSchema):
        """Register a global column mapping."""
        self.column_mappings[column.standard_name.lower()] = column

    def get_stats(self) -> Dict:
        """Get statistics about loaded schemas."""
        return {
            "strands_count": len(self.strands),
            "strand_ids": list(self.strands.keys()),
            "global_columns_count": len(self.column_mappings),
            "data_types_per_strand": {
                sid: len(s.data_types)
                for sid, s in self.strands.items()
            }
        }
