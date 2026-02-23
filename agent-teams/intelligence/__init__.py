"""
Intelligence Module

Self-thinking, reasoning agents with YAML-configurable rules,
confidence scoring, and full audit trails.
"""

from .confidence import (
    ConfidenceLevel,
    ConfidenceThresholds,
    get_action_for_confidence,
)
from .reasoning_trail import (
    ReasoningStep,
    ReasoningTrail,
    ReasoningTrailManager,
)
from .decision_context import (
    DecisionContext,
    ContextType,
)
from .rule_registry import (
    Rule,
    RuleRegistry,
)
from .schema_registry import (
    SchemaRegistry,
    StrandSchema,
    ColumnSchema as StrandColumnSchema,
)
from .learning import (
    Correction,
    LearningEngine,
)
from .inference_engine import (
    InferenceResult,
    InferenceEngine,
)
from .template_registry import (
    TemplateRegistry,
    TemplateFormatter,
    TemplateWriter,
    TemplateSchema,
    SheetSchema,
    ColumnSchema as TemplateColumnSchema,
    get_template_columns,
    format_for_template,
)
from .config_loader import (
    ConfigLoader,
    get_config_loader,
    reset_config_loader,
)
from .fuzzy_matcher import (
    FuzzyMatcher,
    MatchResult,
    get_default_fuzzy_matcher,
    DEFAULT_ABBREVIATIONS,
)

__all__ = [
    # Confidence
    'ConfidenceLevel',
    'ConfidenceThresholds',
    'get_action_for_confidence',
    # Reasoning
    'ReasoningStep',
    'ReasoningTrail',
    'ReasoningTrailManager',
    # Context
    'DecisionContext',
    'ContextType',
    # Rules
    'Rule',
    'RuleRegistry',
    # Strand Schemas
    'SchemaRegistry',
    'StrandSchema',
    'StrandColumnSchema',
    # Learning
    'Correction',
    'LearningEngine',
    # Inference
    'InferenceResult',
    'InferenceEngine',
    # Template Registry
    'TemplateRegistry',
    'TemplateFormatter',
    'TemplateWriter',
    'TemplateSchema',
    'SheetSchema',
    'TemplateColumnSchema',
    'get_template_columns',
    'format_for_template',
    # Config Loader
    'ConfigLoader',
    'get_config_loader',
    'reset_config_loader',
    # Fuzzy Matcher
    'FuzzyMatcher',
    'MatchResult',
    'get_default_fuzzy_matcher',
    'DEFAULT_ABBREVIATIONS',
]
