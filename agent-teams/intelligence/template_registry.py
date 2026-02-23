"""
Template Registry Module
Loads template schemas and formats output to match official IMP Planner templates.
"""

import os
import yaml
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path


@dataclass
class ColumnSchema:
    """Schema for a single column in a template sheet."""
    name: str
    required: bool = True
    max_length: Optional[int] = None
    data_type: str = "string"  # string, boolean, integer, decimal, date
    default: Any = None
    format: Optional[str] = None  # uppercase, 4_digits, DD/MM/YYYY, etc.
    valid_values: Optional[List[str]] = None
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class SheetSchema:
    """Schema for a template sheet."""
    name: str
    description: str
    columns: List[ColumnSchema]

    def get_column_names(self) -> List[str]:
        """Get list of column names in order."""
        return [col.name for col in self.columns]

    def get_required_columns(self) -> List[str]:
        """Get list of required column names."""
        return [col.name for col in self.columns if col.required]


@dataclass
class TemplateSchema:
    """Schema for a complete strand template."""
    strand_id: str
    template_file: str
    template_version: str
    sheets: Dict[str, SheetSchema]


class TemplateRegistry:
    """Registry for loading and managing template schemas."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize template registry with optional config path."""
        if config_path is None:
            # Default to config/templates/template_schemas.yaml relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "templates" / "template_schemas.yaml"

        self.config_path = Path(config_path)
        self.templates: Dict[str, TemplateSchema] = {}
        self._load_templates()

    def _load_templates(self):
        """Load template schemas from YAML file."""
        if not self.config_path.exists():
            print(f"[WARN] Template schema file not found: {self.config_path}")
            return

        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for strand_id, strand_data in data.items():
            if isinstance(strand_data, dict) and 'sheets' in strand_data:
                self.templates[strand_id] = self._parse_template(strand_id, strand_data)

    def _parse_template(self, strand_id: str, data: Dict) -> TemplateSchema:
        """Parse a single template schema from YAML data."""
        sheets = {}

        for sheet_name, sheet_data in data.get('sheets', {}).items():
            columns = []
            for col_data in sheet_data.get('columns', []):
                col = ColumnSchema(
                    name=col_data.get('name'),
                    required=col_data.get('required', True),
                    max_length=col_data.get('max_length'),
                    data_type=col_data.get('type', 'string'),
                    default=col_data.get('default'),
                    format=col_data.get('format'),
                    valid_values=col_data.get('valid_values'),
                    description=col_data.get('description'),
                    min_value=col_data.get('min'),
                    max_value=col_data.get('max')
                )
                columns.append(col)

            sheets[sheet_name] = SheetSchema(
                name=sheet_name,
                description=sheet_data.get('description', ''),
                columns=columns
            )

        return TemplateSchema(
            strand_id=strand_id,
            template_file=data.get('template_file', ''),
            template_version=data.get('template_version', ''),
            sheets=sheets
        )

    def get_template(self, strand_id: str) -> Optional[TemplateSchema]:
        """Get template schema for a strand."""
        return self.templates.get(strand_id)

    def get_sheet_schema(self, strand_id: str, sheet_name: str) -> Optional[SheetSchema]:
        """Get schema for a specific sheet."""
        template = self.templates.get(strand_id)
        if template:
            return template.sheets.get(sheet_name)
        return None

    def get_sheet_columns(self, strand_id: str, sheet_name: str) -> List[str]:
        """Get ordered column names for a sheet."""
        schema = self.get_sheet_schema(strand_id, sheet_name)
        if schema:
            return schema.get_column_names()
        return []

    def list_sheets(self, strand_id: str) -> List[str]:
        """List all sheets for a strand."""
        template = self.templates.get(strand_id)
        if template:
            return list(template.sheets.keys())
        return []


class TemplateFormatter:
    """Formats DataFrames to match template schemas."""

    def __init__(self, registry: Optional[TemplateRegistry] = None):
        """Initialize formatter with optional registry."""
        self.registry = registry or TemplateRegistry()

    def format_dataframe(self, df: pd.DataFrame, strand_id: str, sheet_name: str,
                        column_mapping: Optional[Dict[str, str]] = None) -> Tuple[pd.DataFrame, List[str]]:
        """
        Format a DataFrame to match the template schema.

        Args:
            df: Input DataFrame
            strand_id: Strand ID (S1, S2, S3)
            sheet_name: Target sheet name
            column_mapping: Optional mapping from source columns to template columns

        Returns:
            Tuple of (formatted DataFrame, list of warnings)
        """
        warnings = []
        schema = self.registry.get_sheet_schema(strand_id, sheet_name)

        if not schema:
            warnings.append(f"No schema found for {strand_id}/{sheet_name}")
            return df, warnings

        # Apply column mapping if provided
        if column_mapping:
            df = df.rename(columns=column_mapping)

        # Create output DataFrame with correct column order
        output_columns = schema.get_column_names()
        output_df = pd.DataFrame()

        for col_schema in schema.columns:
            col_name = col_schema.name

            if col_name in df.columns:
                # Column exists, format it
                output_df[col_name] = self._format_column(
                    df[col_name], col_schema, warnings
                )
            elif col_schema.required:
                # Required column missing
                if col_schema.default is not None:
                    output_df[col_name] = col_schema.default
                    warnings.append(f"Required column '{col_name}' missing, using default: {col_schema.default}")
                else:
                    output_df[col_name] = None
                    warnings.append(f"Required column '{col_name}' missing with no default")
            else:
                # Optional column missing, use default or None
                output_df[col_name] = col_schema.default

        return output_df, warnings

    def _format_column(self, series: pd.Series, schema: ColumnSchema,
                      warnings: List[str]) -> pd.Series:
        """Format a single column according to its schema."""
        result = series.copy()
        col_name = schema.name

        # Handle data type conversion
        if schema.data_type == 'boolean':
            result = self._convert_to_boolean(result)
        elif schema.data_type == 'integer':
            result = pd.to_numeric(result, errors='coerce').fillna(0).astype(int)
        elif schema.data_type == 'decimal':
            result = pd.to_numeric(result, errors='coerce')
        elif schema.data_type == 'date':
            result = self._format_date(result, schema.format)

        # Apply format rules
        if schema.format == 'uppercase' and schema.data_type == 'string':
            result = result.astype(str).str.upper()
        elif schema.format == '4_digits' and schema.data_type == 'string':
            result = result.apply(lambda x: str(x).zfill(4) if pd.notna(x) else x)

        # Validate length
        if schema.max_length and schema.data_type == 'string':
            over_length = result.astype(str).str.len() > schema.max_length
            if over_length.any():
                count = over_length.sum()
                warnings.append(f"Column '{col_name}': {count} values exceed max length {schema.max_length}")
                result = result.astype(str).str[:schema.max_length]

        # Validate values
        if schema.valid_values:
            invalid = ~result.isin(schema.valid_values + [None, ''])
            if invalid.any():
                invalid_vals = result[invalid].unique()[:5]
                warnings.append(f"Column '{col_name}': Invalid values found: {list(invalid_vals)}")

        # Validate range
        if schema.min_value is not None:
            below_min = pd.to_numeric(result, errors='coerce') < schema.min_value
            if below_min.any():
                warnings.append(f"Column '{col_name}': {below_min.sum()} values below minimum {schema.min_value}")

        if schema.max_value is not None:
            above_max = pd.to_numeric(result, errors='coerce') > schema.max_value
            if above_max.any():
                warnings.append(f"Column '{col_name}': {above_max.sum()} values above maximum {schema.max_value}")

        return result

    def _convert_to_boolean(self, series: pd.Series) -> pd.Series:
        """Convert various boolean representations to True/False."""
        bool_map = {
            'true': True, 'false': False,
            'TRUE': True, 'FALSE': False,
            'True': True, 'False': False,
            'yes': True, 'no': False,
            'YES': True, 'NO': False,
            'Yes': True, 'No': False,
            '1': True, '0': False,
            1: True, 0: False,
            1.0: True, 0.0: False
        }
        return series.map(lambda x: bool_map.get(x, x) if pd.notna(x) else False)

    def _format_date(self, series: pd.Series, date_format: Optional[str] = None) -> pd.Series:
        """Format date values."""
        if date_format is None:
            date_format = "DD/MM/YYYY"

        # Convert to datetime
        result = pd.to_datetime(series, errors='coerce', dayfirst=True)

        # Format as string
        if date_format == "DD/MM/YYYY":
            return result.dt.strftime('%d/%m/%Y')
        elif date_format == "YYYY/YY":
            return result.dt.strftime('%Y/%y')
        else:
            return result.dt.strftime('%d/%m/%Y')

    def validate_dataframe(self, df: pd.DataFrame, strand_id: str,
                          sheet_name: str) -> List[str]:
        """
        Validate a DataFrame against the template schema.

        Returns list of validation errors.
        """
        errors = []
        schema = self.registry.get_sheet_schema(strand_id, sheet_name)

        if not schema:
            errors.append(f"No schema found for {strand_id}/{sheet_name}")
            return errors

        # Check required columns
        for col_schema in schema.columns:
            if col_schema.required:
                if col_schema.name not in df.columns:
                    errors.append(f"Missing required column: {col_schema.name}")
                elif df[col_schema.name].isna().all():
                    errors.append(f"Required column '{col_schema.name}' is entirely empty")

        # Check for unexpected columns
        expected_cols = set(schema.get_column_names())
        actual_cols = set(df.columns)
        extra_cols = actual_cols - expected_cols
        if extra_cols:
            errors.append(f"Unexpected columns: {list(extra_cols)}")

        return errors


class TemplateWriter:
    """Writes formatted data to Excel templates."""

    def __init__(self, template_dir: Optional[str] = None,
                 registry: Optional[TemplateRegistry] = None):
        """Initialize writer with template directory."""
        if template_dir is None:
            project_root = Path(__file__).parent.parent
            template_dir = project_root / "knowledge" / "Templates"

        self.template_dir = Path(template_dir)
        self.registry = registry or TemplateRegistry()
        self.formatter = TemplateFormatter(self.registry)

    def get_template_path(self, strand_id: str) -> Optional[Path]:
        """Get path to template file for a strand."""
        template = self.registry.get_template(strand_id)
        if not template:
            return None

        strand_folder = f"Strand {strand_id[1]}"  # S1 -> "Strand 1"
        return self.template_dir / strand_folder / template.template_file

    def write_to_template(self, data: Dict[str, pd.DataFrame], strand_id: str,
                         output_path: str, column_mappings: Optional[Dict[str, Dict]] = None) -> Dict[str, Any]:
        """
        Write data to a new Excel file matching the template format.

        Args:
            data: Dict mapping sheet names to DataFrames
            strand_id: Strand ID (S1, S2, S3)
            output_path: Path for output file
            column_mappings: Optional dict of sheet_name -> column_mapping

        Returns:
            Dict with status, warnings, and errors
        """
        result = {
            'status': 'success',
            'sheets_written': [],
            'warnings': [],
            'errors': []
        }

        template = self.registry.get_template(strand_id)
        if not template:
            result['status'] = 'error'
            result['errors'].append(f"No template found for strand {strand_id}")
            return result

        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, df in data.items():
                    if sheet_name not in template.sheets:
                        result['warnings'].append(f"Sheet '{sheet_name}' not in template schema, writing as-is")
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        result['sheets_written'].append(sheet_name)
                        continue

                    # Get column mapping for this sheet
                    col_mapping = None
                    if column_mappings and sheet_name in column_mappings:
                        col_mapping = column_mappings[sheet_name]

                    # Format DataFrame
                    formatted_df, warnings = self.formatter.format_dataframe(
                        df, strand_id, sheet_name, col_mapping
                    )

                    result['warnings'].extend([f"{sheet_name}: {w}" for w in warnings])

                    # Validate
                    errors = self.formatter.validate_dataframe(formatted_df, strand_id, sheet_name)
                    result['errors'].extend([f"{sheet_name}: {e}" for e in errors])

                    # Write to Excel
                    formatted_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    result['sheets_written'].append(sheet_name)

            if result['errors']:
                result['status'] = 'completed_with_errors'
            elif result['warnings']:
                result['status'] = 'completed_with_warnings'

        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(str(e))

        return result


# Convenience function for quick access
def get_template_columns(strand_id: str, sheet_name: str) -> List[str]:
    """Get column names for a template sheet."""
    registry = TemplateRegistry()
    return registry.get_sheet_columns(strand_id, sheet_name)


def format_for_template(df: pd.DataFrame, strand_id: str, sheet_name: str,
                       column_mapping: Optional[Dict[str, str]] = None) -> Tuple[pd.DataFrame, List[str]]:
    """Format a DataFrame for a template sheet."""
    formatter = TemplateFormatter()
    return formatter.format_dataframe(df, strand_id, sheet_name, column_mapping)
