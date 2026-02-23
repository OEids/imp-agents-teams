"""
Expert Agents

Agents enhanced with IMP Planner domain knowledge.
Each agent uses specialized knowledge to make informed decisions
and provide expert-level validation and transformation.

Enhanced with InferenceEngine for:
- Intelligent column mapping with confidence scoring
- Role/pension classification with reasoning trails
- Configurable validation thresholds
- Learning from user corrections
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from .base import (
    BaseAgent, CheckInReport, AnalyzeAgent, CleanAgent,
    TransformAgent, BuildAgent, QualityCheckAgent, AuditorAgent, AgentTeam
)
from .validation import DataValidator, AssumptionTracker
from .knowledge import (
    get_team_knowledge, TeamKnowledge,
    normalize_finance_code, normalize_scale_point,
    calculate_fte, calculate_tto_paid_weeks,
    validate_salary_vs_scale, is_teaching_role, is_support_role,
    PAY_SCALES_2024_25, TTO_LEAVE_ENTITLEMENTS,
    # S2 Domain Knowledge integration
    S2_DOMAIN_KNOWLEDGE_AVAILABLE,
    parse_combined_field,
    extract_finance_code,
    transform_contract_row,
    S2_PAY_SCALES,
    STAFF_ROLE_GROUPS,
    EQUATED_WEEK_PATTERNS,
    COMBINED_COLUMNS,
    get_finance_codes_for_role_group,
    map_role_title_to_group,
    get_default_pension,
    get_default_fund_code,
)
from .payscale_extractor import PayScaleExtractor, extract_payscales_from_folder, get_default_payscales_folder

# Import Intelligence Module for smart decisions
try:
    from intelligence import (
        InferenceEngine, InferenceResult, DecisionContext,
        ConfidenceLevel, ReasoningTrailManager
    )
    INFERENCE_AVAILABLE = True
except ImportError:
    INFERENCE_AVAILABLE = False


# Shared InferenceEngine instance for all expert agents
_inference_engine: Optional['InferenceEngine'] = None


def get_inference_engine() -> Optional['InferenceEngine']:
    """Get or create the shared InferenceEngine instance."""
    global _inference_engine
    if _inference_engine is None and INFERENCE_AVAILABLE:
        try:
            _inference_engine = InferenceEngine(hot_reload=False)
        except Exception:
            pass
    return _inference_engine


class ExpertAnalyzeAgent(AnalyzeAgent):
    """Analyze agent with domain expertise."""

    def __init__(self, team_id: str, team_config: Dict):
        super().__init__(team_id, team_config)
        self.knowledge = get_team_knowledge(team_id)
        # Storage for extracted pay scales (S2 specific)
        self.extracted_payscales = None
        self.extracted_allowances = None
        self.payscale_extraction_log = []

    def execute(self, input_data: Path) -> CheckInReport:
        """Analyze with expert knowledge."""
        self.log(f"Expert analysis of {input_data}")
        self.log(f"Using {self.knowledge.team_name} expertise")

        # Run base analysis first
        report = super().execute(input_data)

        # =====================================================================
        # S2 SPECIFIC: Auto-extract pay scales from payscales folder
        # =====================================================================
        if self.team_id == "S2":
            payscale_results = self._extract_payscales_if_available()
            if payscale_results:
                report.details["payscale_extraction"] = payscale_results
                self.log(f"Pay scale extraction: {payscale_results.get('summary', 'completed')}")

        # Add expert analysis
        if self.data is not None and not self.data.empty:
            expert_insights = self._apply_expert_analysis(self.data)
            report.details["expert_insights"] = expert_insights

            # Add knowledge-based assumptions
            self._add_knowledge_assumptions()

            # Update recommendations with expert guidance
            report.recommendations.extend(self._get_expert_recommendations())

        return report

    def _extract_payscales_if_available(self) -> Optional[Dict]:
        """
        Automatically extract pay scales from the payscales folder if it exists.
        This ensures pay scale data is always captured during S2 processing.
        """
        # Try multiple possible locations for payscales
        data_dir = self.team_config.get("data_dir", ".")
        if isinstance(data_dir, str):
            data_dir = Path(data_dir)

        possible_paths = [
            get_default_payscales_folder(),  # knowledge/S2/payscales example
            Path(__file__).parent.parent / "knowledge" / "S2" / "payscales",
            Path(__file__).parent.parent / "knowledge" / "S2" / "pay_scales",
            data_dir / "payscales",
        ]

        payscales_folder = None
        for path in possible_paths:
            if path.exists() and list(path.glob("*.xlsx")):
                payscales_folder = path
                break

        if not payscales_folder:
            self.log("No payscales folder found - skipping pay scale extraction")
            return {
                "status": "skipped",
                "reason": "No payscales folder with xlsx files found",
                "searched_paths": [str(p) for p in possible_paths]
            }

        try:
            self.log(f"Extracting pay scales from: {payscales_folder}")

            # Run the extractor
            result = extract_payscales_from_folder(payscales_folder)

            # Store extracted data for use by other agents
            self.extracted_payscales = result.get('pay_scales', [])
            self.extracted_allowances = result.get('allowances', [])
            self.payscale_extraction_log = result.get('logs', [])

            # Build summary
            ps_count = len(self.extracted_payscales)
            ps_points = sum(len(ps.points) for ps in self.extracted_payscales)
            allow_count = len(self.extracted_allowances)
            allow_points = sum(len(a.points) for a in self.extracted_allowances)

            if ps_count == 0 and allow_count == 0:
                self.log("WARNING: No pay scales were imported from the files!")
                return {
                    "status": "warning",
                    "reason": "No pay scales were imported - check file formats",
                    "folder": str(payscales_folder),
                    "files_processed": len(list(payscales_folder.glob("*.xlsx"))),
                    "logs": self.payscale_extraction_log[-10:]  # Last 10 log entries
                }

            summary = f"{ps_count} pay scales ({ps_points} points), {allow_count} allowances ({allow_points} points)"
            self.log(f"Extracted: {summary}")

            # Add assumption about extracted pay scales
            self.assumptions.add(
                category="data_source",
                description=f"Extracted {ps_count} pay scales from {payscales_folder.name}",
                reason="Pay scale files found in designated folder",
                impact="Pay scale validation will use extracted rates",
                confidence="high",
                affected_records=ps_points
            )

            return {
                "status": "success",
                "folder": str(payscales_folder),
                "summary": summary,
                "pay_scales": [
                    {
                        "code": ps.code,
                        "title": ps.title,
                        "type": ps.scale_type,
                        "points_count": len(ps.points),
                        "sample_points": [
                            {"code": p.code, "rate": p.rate}
                            for p in ps.points[:3]
                        ]
                    }
                    for ps in self.extracted_payscales
                ],
                "allowances": [
                    {
                        "code": a.code,
                        "title": a.title,
                        "points_count": len(a.points),
                        "sample_points": [
                            {"code": p.code, "amount": p.amount}
                            for p in a.points[:3]
                        ]
                    }
                    for a in self.extracted_allowances
                ],
                "grades": result.get('grades', [])
            }

        except FileNotFoundError as e:
            self.log(f"Pay scale folder not found: {e}")
            return {"status": "error", "reason": str(e)}
        except ValueError as e:
            self.log(f"No xlsx files in payscales folder: {e}")
            return {"status": "error", "reason": str(e)}
        except Exception as e:
            self.log(f"Error extracting pay scales: {e}")
            return {"status": "error", "reason": str(e)}

    def _apply_expert_analysis(self, df: pd.DataFrame) -> Dict:
        """Apply domain-specific analysis."""
        insights = {
            "recognized_columns": [],
            "missing_required_columns": [],
            "data_type_issues": [],
            "domain_specific_findings": []
        }

        # Match columns against known mappings
        df_cols_lower = {str(c).lower(): c for c in df.columns}

        for mapping in self.knowledge.column_mappings:
            found = False
            for variation in mapping.variations:
                if variation.lower() in df_cols_lower:
                    insights["recognized_columns"].append({
                        "source": df_cols_lower[variation.lower()],
                        "maps_to": mapping.standard_name,
                        "required": mapping.required
                    })
                    found = True
                    break

            if not found and mapping.required:
                insights["missing_required_columns"].append({
                    "field": mapping.standard_name,
                    "expected_variations": mapping.variations[:5],
                    "hint": mapping.format_hint
                })

        # Team-specific analysis
        if self.team_id == "S1":
            insights["domain_specific_findings"].extend(self._analyze_s1_data(df))
        elif self.team_id == "S2":
            insights["domain_specific_findings"].extend(self._analyze_s2_data(df))
        elif self.team_id == "S3":
            insights["domain_specific_findings"].extend(self._analyze_s3_data(df))

        return insights

    def _analyze_s1_data(self, df: pd.DataFrame) -> List[Dict]:
        """S1-specific analysis: COA structure."""
        findings = []

        # Look for finance codes
        finance_cols = [c for c in df.columns if any(
            v in str(c).lower() for v in ['code', 'nominal', 'account', 'ledger']
        )]

        if finance_cols:
            sample = df[finance_cols[0]].dropna().head(100)
            # Check format
            lengths = sample.astype(str).str.len()
            if lengths.mode().iloc[0] if len(lengths.mode()) > 0 else 0 == 6:
                findings.append({
                    "type": "format_issue",
                    "finding": "Finance codes appear to be 6 digits - need normalizing to 4",
                    "column": finance_cols[0],
                    "action": "Will normalize to 4 digits during transformation"
                })
            elif lengths.mode().iloc[0] if len(lengths.mode()) > 0 else 0 == 4:
                findings.append({
                    "type": "format_ok",
                    "finding": "Finance codes already in correct 4-digit format",
                    "column": finance_cols[0]
                })

        # Check for cost centres
        cc_cols = [c for c in df.columns if any(
            v in str(c).lower() for v in ['cost centre', 'site', 'school', 'location']
        )]

        if cc_cols:
            unique_cc = df[cc_cols[0]].dropna().unique()
            findings.append({
                "type": "reference_data",
                "finding": f"Found {len(unique_cc)} unique cost centres",
                "samples": list(unique_cc[:10])
            })

        return findings

    def _analyze_s2_data(self, df: pd.DataFrame) -> List[Dict]:
        """S2-specific analysis: Staff data."""
        findings = []

        # Check for payroll numbers
        payroll_cols = [c for c in df.columns if any(
            v in str(c).lower() for v in ['payroll', 'employee', 'staff id']
        )]

        if payroll_cols:
            unique_staff = df[payroll_cols[0]].dropna().nunique()
            total_rows = len(df)
            findings.append({
                "type": "data_structure",
                "finding": f"Found {unique_staff} unique staff across {total_rows} rows",
                "implication": "Multiple rows per person indicates multiple contracts" if total_rows > unique_staff else "One row per person"
            })

        # Check for pay scale info
        scale_cols = [c for c in df.columns if any(
            v in str(c).lower() for v in ['scale', 'pay', 'spine', 'point']
        )]

        if scale_cols:
            sample = df[scale_cols[0]].dropna().head(50).astype(str)
            teaching_count = sum(1 for s in sample if any(
                t in s.upper() for t in ['MPS', 'UPS', 'MAIN', 'UPPER', 'LEADERSHIP', 'M1', 'U1', 'L']
            ))
            support_count = sum(1 for s in sample if any(
                t in s.upper() for t in ['NJC', 'SCP', 'POINT', 'SPINE']
            ) or s.isdigit())

            findings.append({
                "type": "staff_composition",
                "finding": f"Detected {teaching_count} teaching scale entries, {support_count} support scale entries in sample",
                "column": scale_cols[0]
            })

        # Check salary data
        salary_cols = [c for c in df.columns if 'salary' in str(c).lower()]
        if salary_cols:
            salaries = pd.to_numeric(df[salary_cols[0]], errors='coerce').dropna()
            if len(salaries) > 0:
                findings.append({
                    "type": "salary_range",
                    "finding": f"Salary range: £{salaries.min():,.0f} - £{salaries.max():,.0f}",
                    "median": f"£{salaries.median():,.0f}",
                    "count": len(salaries)
                })

        return findings

    def _analyze_s3_data(self, df: pd.DataFrame) -> List[Dict]:
        """S3-specific analysis: Financial data."""
        findings = []

        # Check for budget amounts
        amount_cols = [c for c in df.columns if any(
            v in str(c).lower() for v in ['amount', 'value', 'budget', 'total']
        )]

        if amount_cols:
            amounts = pd.to_numeric(df[amount_cols[0]], errors='coerce').dropna()
            if len(amounts) > 0:
                income = amounts[amounts > 0].sum()
                expenditure = abs(amounts[amounts < 0].sum())
                findings.append({
                    "type": "budget_summary",
                    "finding": f"Total income: £{income:,.0f}, Total expenditure: £{expenditure:,.0f}",
                    "balance": f"£{income - expenditure:,.0f}"
                })

        return findings

    def _add_knowledge_assumptions(self):
        """Add assumptions based on domain knowledge."""
        for concept, definition in list(self.knowledge.key_concepts.items())[:5]:
            self.assumptions.add(
                category="domain_knowledge",
                description=f"Using standard definition for '{concept}'",
                reason=definition,
                impact="Processing will follow IMP Planner standards",
                confidence="high"
            )

    def _get_expert_recommendations(self) -> List[str]:
        """Get recommendations based on knowledge."""
        recommendations = []

        # Add common issue awareness
        if self.knowledge.common_issues:
            recommendations.append(
                f"Watch for common issues: {', '.join(self.knowledge.common_issues[:3])}"
            )

        return recommendations


class ExpertCleanAgent(CleanAgent):
    """Clean agent with domain expertise."""

    def __init__(self, team_id: str, team_config: Dict):
        super().__init__(team_id, team_config)
        self.knowledge = get_team_knowledge(team_id)

    def execute(self, input_data: Dict) -> CheckInReport:
        """Clean with expert knowledge."""
        self.log(f"Expert cleaning using {self.knowledge.team_name} knowledge")

        original_df = input_data.get("original_data")
        if original_df is None or original_df.empty:
            return super().execute(input_data)

        # Capture original for comparison
        self.comparator.capture_original(original_df)

        details = {
            "records_input": len(original_df),
            "records_output": 0,
            "expert_normalizations": [],
            "cleaning_actions": []
        }

        df = original_df.copy()

        # 1. Apply column name normalization using knowledge
        df, col_changes = self._normalize_column_names(df)
        details["expert_normalizations"].extend(col_changes)

        # 2. Apply team-specific cleaning
        if self.team_id == "S1":
            df, s1_changes = self._clean_s1_data(df)
            details["cleaning_actions"].extend(s1_changes)
        elif self.team_id == "S2":
            df, s2_changes = self._clean_s2_data(df)
            details["cleaning_actions"].extend(s2_changes)
        elif self.team_id == "S3":
            df, s3_changes = self._clean_s3_data(df)
            details["cleaning_actions"].extend(s3_changes)

        # 3. Standard cleaning
        df = df.dropna(how='all')
        df = df.drop_duplicates()

        details["records_output"] = len(df)

        # Compare
        comparison = self.comparator.compare(df)
        self.metadata["comparison"] = comparison

        # Validate
        self.validator.validate_all(df)

        self.data = df
        self.metadata.update({
            "cleaned_data": df,
            "original_data": original_df,
            "comparison": comparison
        })

        return self.create_report(
            status="success" if not self.issues else "warning",
            summary=f"Expert cleaned {details['records_input']} -> {details['records_output']} records. {len(details['expert_normalizations'])} expert normalizations applied.",
            details=details,
            recommendations=self._get_cleaning_recommendations()
        )

    def _normalize_column_names(self, df: pd.DataFrame) -> tuple:
        """
        Normalize column names using knowledge base and InferenceEngine.

        Uses InferenceEngine when available for:
        - Confidence-scored column mapping
        - Full reasoning trails
        - Learning from corrections
        """
        changes = []
        new_columns = {}
        inference_engine = get_inference_engine()

        for col in df.columns:
            col_lower = str(col).strip().lower()
            mapped = False

            # Try InferenceEngine first for intelligent mapping
            if inference_engine and not mapped:
                result = inference_engine.infer_column_mapping(
                    source_column=str(col),
                    strand=self.team_id
                )

                if result.decision != str(col) and result.confidence >= 0.5:
                    new_columns[col] = result.decision
                    changes.append({
                        "original": str(col),
                        "normalized": result.decision,
                        "confidence": result.confidence,
                        "reasoning": result.reasoning[0] if result.reasoning else "Rule-based mapping",
                        "requires_review": result.requires_review
                    })
                    self.assumptions.add_mapping_assumption(
                        source_col=str(col),
                        target_col=result.decision,
                        mapping_type="inference_engine"
                    )

                    # Log if low confidence
                    if result.requires_review:
                        self.log(f"⚠ Low confidence mapping: {col} → {result.decision} ({result.confidence:.0%})")

                    mapped = True

            # Fallback to knowledge base matching
            if not mapped:
                for mapping in self.knowledge.column_mappings:
                    if col_lower in [v.lower() for v in mapping.variations] or col_lower == mapping.standard_name.lower():
                        if str(col) != mapping.standard_name:
                            new_columns[col] = mapping.standard_name
                            changes.append({
                                "original": str(col),
                                "normalized": mapping.standard_name,
                                "confidence": 0.9,
                                "reasoning": "Matched to IMP Planner standard",
                                "requires_review": False
                            })
                            self.assumptions.add_mapping_assumption(
                                source_col=str(col),
                                target_col=mapping.standard_name,
                                mapping_type="knowledge_based"
                            )
                        break

        if new_columns:
            df = df.rename(columns=new_columns)

        return df, changes

    def _clean_s1_data(self, df: pd.DataFrame) -> tuple:
        """S1-specific cleaning: Finance codes, cost centres."""
        changes = []

        # Normalize finance codes to 4 digits
        if 'finance_code' in df.columns:
            original = df['finance_code'].copy()
            df['finance_code'] = df['finance_code'].apply(
                lambda x: normalize_finance_code(x) if pd.notna(x) else x
            )
            changed_count = (df['finance_code'] != original.astype(str)).sum()
            if changed_count > 0:
                changes.append(f"Normalized {changed_count} finance codes to 4-digit format")
                self.assumptions.add(
                    category="format",
                    description=f"Normalized {changed_count} finance codes to 4-digit format",
                    reason="IMP Planner requires 4-digit finance codes with leading zeros",
                    impact="Codes now match expected format",
                    confidence="high",
                    affected_records=changed_count
                )

        # Normalize cost centres to uppercase
        if 'cost_centre' in df.columns:
            df['cost_centre'] = df['cost_centre'].astype(str).str.upper().str.strip()
            df['cost_centre'] = df['cost_centre'].replace('NAN', np.nan)
            changes.append("Normalized cost centres to uppercase")

        # Normalize departments to 3 digits
        if 'department' in df.columns:
            df['department'] = df['department'].apply(
                lambda x: str(int(float(x))).zfill(3) if pd.notna(x) and str(x).replace('.', '').isdigit() else x
            )
            changes.append("Normalized department codes to 3-digit format")

        return df, changes

    def _clean_s2_data(self, df: pd.DataFrame) -> tuple:
        """S2-specific cleaning: Staff data, pay scales, combined field parsing."""
        changes = []

        # =====================================================================
        # CRITICAL: Parse Combined Fields (S2 Domain Knowledge Integration)
        # =====================================================================
        # Import files use "CODE: Title (extra)" format that must be parsed
        if S2_DOMAIN_KNOWLEDGE_AVAILABLE:
            combined_cols_found = []
            for col in df.columns:
                if col in COMBINED_COLUMNS or 'Combined' in str(col):
                    combined_cols_found.append(col)

            if combined_cols_found:
                self.log(f"Parsing {len(combined_cols_found)} combined format columns")
                for col in combined_cols_found:
                    # Create code column (extract just the code part)
                    code_col = col.replace(' Combined', '_Code').replace(' Code', '_Code')
                    if code_col == col:
                        code_col = col + '_Parsed'

                    df[code_col] = df[col].apply(
                        lambda x: parse_combined_field(str(x))[0] if pd.notna(x) else ''
                    )
                    changes.append(f"Parsed combined field '{col}' -> '{code_col}'")

                self.assumptions.add(
                    category="format",
                    description=f"Parsed {len(combined_cols_found)} combined format columns",
                    reason="Import files use 'CODE: Title' format that needs parsing",
                    impact="Codes extracted for matching and validation",
                    confidence="high",
                    affected_records=len(df)
                )

        # =====================================================================
        # Map Role Titles to Role Groups (if role group not already present)
        # =====================================================================
        if S2_DOMAIN_KNOWLEDGE_AVAILABLE and 'job_title' in df.columns:
            if 'staff_role_group' not in df.columns and 'Staff Role Group' not in df.columns:
                df['staff_role_group'] = df['job_title'].apply(
                    lambda x: map_role_title_to_group(str(x)) if pd.notna(x) else None
                )
                mapped_count = df['staff_role_group'].notna().sum()
                if mapped_count > 0:
                    changes.append(f"Mapped {mapped_count} role titles to role groups")
                    self.assumptions.add(
                        category="classification",
                        description=f"Mapped {mapped_count} job titles to staff role groups",
                        reason="Role groups determine finance code mappings",
                        impact="Finance codes will be derived from role group",
                        confidence="medium",
                        affected_records=mapped_count
                    )

        # =====================================================================
        # Derive Finance Codes from Role Groups (S2 Domain Knowledge)
        # =====================================================================
        if S2_DOMAIN_KNOWLEDGE_AVAILABLE and 'staff_role_group' in df.columns:
            # Add finance code columns if not present
            if 'gross_salary_finance_code' not in df.columns:
                df['gross_salary_finance_code'] = df['staff_role_group'].apply(
                    lambda x: get_finance_codes_for_role_group(x).get('gross_salary', '') if x else ''
                )
                df['employers_ni_finance_code'] = df['staff_role_group'].apply(
                    lambda x: get_finance_codes_for_role_group(x).get('employers_ni', '') if x else ''
                )
                df['pension_finance_code'] = df['staff_role_group'].apply(
                    lambda x: get_finance_codes_for_role_group(x).get('pension', '') if x else ''
                )
                derived_count = (df['gross_salary_finance_code'] != '').sum()
                if derived_count > 0:
                    changes.append(f"Derived finance codes for {derived_count} records from role groups")
                    self.assumptions.add(
                        category="derivation",
                        description=f"Derived finance codes from staff role groups for {derived_count} records",
                        reason="Role groups have standard finance code mappings",
                        impact="Gross salary, NI, and pension finance codes populated",
                        confidence="high",
                        affected_records=derived_count
                    )

        # =====================================================================
        # Mark Missing Fund Codes and Pension Schemes (NEVER use defaults)
        # =====================================================================
        if S2_DOMAIN_KNOWLEDGE_AVAILABLE:
            # Mark missing fund codes as MISSING (do NOT use defaults)
            if 'fund_code' in df.columns:
                empty_fund = df['fund_code'].isna() | (df['fund_code'] == '')
                if empty_fund.any():
                    df.loc[empty_fund, 'fund_code'] = 'MISSING'
                    changes.append(f"Marked {empty_fund.sum()} records with MISSING fund code")

            # Mark missing pension as MISSING (do NOT use defaults)
            if 'pension_code' in df.columns:
                empty_pension = df['pension_code'].isna() | (df['pension_code'] == '')
                if empty_pension.any():
                    df.loc[empty_pension, 'pension_code'] = 'MISSING'
                    changes.append(f"Marked {empty_pension.sum()} records with MISSING pension code")

        # =====================================================================
        # Normalize pay scale points
        # =====================================================================
        if 'current_scale_point' in df.columns:
            original = df['current_scale_point'].copy()

            def normalize_point(p):
                if pd.isna(p):
                    return p
                scale_type, point_num = normalize_scale_point(str(p))
                if scale_type and point_num:
                    if scale_type == 'MPS':
                        return f'M{point_num}'
                    elif scale_type == 'UPS':
                        return f'U{point_num}'
                    elif scale_type == 'leadership':
                        return f'L{point_num}'
                    elif scale_type == 'NJC':
                        return f'SCP{point_num}'
                return p

            df['current_scale_point'] = df['current_scale_point'].apply(normalize_point)
            changed = (df['current_scale_point'].astype(str) != original.astype(str)).sum()
            if changed > 0:
                changes.append(f"Normalized {changed} pay scale points")
                self.assumptions.add(
                    category="format",
                    description=f"Normalized {changed} pay scale point formats",
                    reason="Standardizing to IMP Planner format (M1, U2, L8, SCP11)",
                    impact="Pay scale matching will be more accurate",
                    confidence="medium",
                    affected_records=changed
                )

        # =====================================================================
        # Calculate FTE if hours present
        # =====================================================================
        if 'weekly_hours' in df.columns and 'full_time_hours' in df.columns:
            if 'weekly_fte' not in df.columns:
                df['weekly_fte'] = df.apply(
                    lambda r: calculate_fte(r['weekly_hours'], r['full_time_hours'])
                    if pd.notna(r['weekly_hours']) and pd.notna(r['full_time_hours']) else np.nan,
                    axis=1
                )
                changes.append("Calculated FTE from hours")
                self.assumptions.add(
                    category="calculation",
                    description="Calculated weekly FTE from weekly_hours / full_time_hours",
                    reason="FTE required for salary calculations",
                    impact="FTE values derived from hours",
                    confidence="high",
                    affected_records=len(df)
                )

        # =====================================================================
        # Determine role type (teaching/support) using InferenceEngine
        # =====================================================================
        if 'job_title' in df.columns and 'role_type' not in df.columns:
            inference_engine = get_inference_engine()

            if inference_engine:
                # Use intelligent classification
                def classify_role_intelligent(job_title):
                    if pd.isna(job_title):
                        return 'unknown'
                    result = inference_engine.infer_classification(
                        value=str(job_title),
                        classification_type="role_type"
                    )
                    return result.decision if result.confidence >= 0.5 else 'unknown'

                df['role_type'] = df['job_title'].apply(classify_role_intelligent)

                # Count classifications
                teaching_count = (df['role_type'] == 'teaching').sum()
                support_count = (df['role_type'] == 'support').sum()
                unknown_count = (df['role_type'] == 'unknown').sum()

                changes.append(f"Classified staff using InferenceEngine: {teaching_count} teaching, {support_count} support, {unknown_count} unknown")

                if unknown_count > 0:
                    self.log(f"⚠ {unknown_count} staff could not be classified - flagged for review")

                self.assumptions.add(
                    category="classification",
                    description=f"Classified {teaching_count + support_count} roles using InferenceEngine rules",
                    reason="Role type determines pay scale and pension scheme",
                    impact="May affect pension validation",
                    confidence="high" if unknown_count == 0 else "medium",
                    affected_records=len(df)
                )
            else:
                # Fallback to legacy classification
                df['role_type'] = df['job_title'].apply(
                    lambda x: 'teaching' if is_teaching_role(x) else 'support' if is_support_role(x) else 'unknown'
                )
                changes.append("Classified staff as teaching/support based on job title (legacy)")
                self.assumptions.add(
                    category="classification",
                    description="Classified roles as teaching/support based on job title keywords",
                    reason="Role type determines pay scale and pension scheme",
                    impact="May affect pension validation",
                    confidence="medium",
                    affected_records=len(df)
                )

        # =====================================================================
        # Normalize finance codes
        # =====================================================================
        if 'finance_code' in df.columns:
            df['finance_code'] = df['finance_code'].apply(
                lambda x: normalize_finance_code(x) if pd.notna(x) else x
            )
            changes.append("Normalized finance codes")

        return df, changes

    def _clean_s3_data(self, df: pd.DataFrame) -> tuple:
        """S3-specific cleaning: Budget data."""
        changes = []

        # Normalize finance codes
        if 'finance_code' in df.columns:
            df['finance_code'] = df['finance_code'].apply(
                lambda x: normalize_finance_code(x) if pd.notna(x) else x
            )
            changes.append("Normalized finance codes to 4-digit format")

        # Standardize amounts
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            changes.append("Converted amounts to numeric")

        return df, changes

    def _get_cleaning_recommendations(self) -> List[str]:
        """Get cleaning recommendations."""
        recommendations = []

        low_conf = self.assumptions.get_low_confidence()
        if low_conf:
            recommendations.append(f"Review {len(low_conf)} low-confidence assumptions")

        return recommendations


class ExpertTransformAgent(TransformAgent):
    """Transform agent with domain expertise."""

    def __init__(self, team_id: str, team_config: Dict):
        super().__init__(team_id, team_config)
        self.knowledge = get_team_knowledge(team_id)

    def _get_template_columns(self) -> List[str]:
        """Get template columns from knowledge base."""
        return [m.standard_name for m in self.knowledge.column_mappings]

    def _get_required_columns(self) -> List[str]:
        """Get required columns from knowledge base."""
        return [m.standard_name for m in self.knowledge.column_mappings if m.required]


class ExpertBuildAgent(BuildAgent):
    """Build agent with domain expertise."""

    def __init__(self, team_id: str, team_config: Dict, template_path: Path):
        super().__init__(team_id, team_config, template_path)
        self.knowledge = get_team_knowledge(team_id)

    def _create_assumptions_summary(self) -> pd.DataFrame:
        """Create enhanced assumptions summary with knowledge context."""
        rows = []

        # Add knowledge-based context header
        rows.append({
            "Category": "KNOWLEDGE BASE",
            "Confidence": "INFO",
            "Description": f"Using {self.knowledge.team_name} expertise",
            "Reason": self.knowledge.description,
            "Impact": f"Processing follows IMP Planner standards for {self.team_id}",
            "Affected Records": 0
        })

        # Add all tracked assumptions
        for a in self.assumptions.assumptions:
            rows.append({
                "Category": a.category,
                "Confidence": a.confidence.upper(),
                "Description": a.description,
                "Reason": a.reason,
                "Impact": a.impact,
                "Affected Records": a.affected_records
            })

        return pd.DataFrame(rows) if rows else pd.DataFrame({"Message": ["No assumptions made"]})


class ExpertQualityCheckAgent(QualityCheckAgent):
    """Quality assurance agent with domain expertise."""

    def __init__(self, team_id: str, team_config: Dict):
        super().__init__(team_id, team_config)
        self.knowledge = get_team_knowledge(team_id)
        # Storage for extracted pay scales from analysis phase
        self.extracted_payscales = None
        self.extracted_allowances = None

    def execute(self, input_data: Dict) -> CheckInReport:
        """Perform expert quality check with domain knowledge."""
        self.log(f"Expert quality assurance using {self.knowledge.team_name} standards")

        # =====================================================================
        # S2 SPECIFIC: Check for extracted pay scales from analysis phase
        # =====================================================================
        if self.team_id == "S2":
            self.extracted_payscales = input_data.get("extracted_payscales")
            self.extracted_allowances = input_data.get("extracted_allowances")
            if self.extracted_payscales:
                self.log(f"Using {len(self.extracted_payscales)} extracted pay scales for validation")
            else:
                # Try to extract if not provided
                payscale_result = self._try_extract_payscales()
                if payscale_result:
                    self.log(f"Extracted pay scales during quality check: {len(self.extracted_payscales or [])} scales")

        # Run base quality check first
        report = super().execute(input_data)

        # Add expert-level checks
        if self.data is not None and not self.data.empty:
            expert_checks = self._apply_expert_quality_checks(self.data)
            report.details["expert_quality_checks"] = expert_checks

            # Update quality score with expert findings
            self._update_quality_with_expert_findings(report, expert_checks)

            # Add domain-specific recommendations
            expert_recommendations = self._get_expert_recommendations(report.details)
            report.recommendations.extend(expert_recommendations)

        return report

    def _try_extract_payscales(self) -> bool:
        """Try to extract pay scales if not already provided."""
        try:
            payscales_folder = get_default_payscales_folder()
            if payscales_folder.exists() and list(payscales_folder.glob("*.xlsx")):
                result = extract_payscales_from_folder(payscales_folder)
                self.extracted_payscales = result.get('pay_scales', [])
                self.extracted_allowances = result.get('allowances', [])
                return True
        except Exception as e:
            self.log(f"Could not extract pay scales: {e}")
        return False

    def _apply_expert_quality_checks(self, df: pd.DataFrame) -> Dict:
        """Apply domain-specific quality checks."""
        checks = {
            "domain_validation": [],
            "business_rule_compliance": [],
            "data_completeness": [],
            "format_validation": []
        }

        # Team-specific expert checks
        if self.team_id == "S1":
            checks["domain_validation"].extend(self._validate_s1_quality(df))
        elif self.team_id == "S2":
            checks["domain_validation"].extend(self._validate_s2_quality(df))
        elif self.team_id == "S3":
            checks["domain_validation"].extend(self._validate_s3_quality(df))

        # Validate against knowledge base rules
        for rule in self.knowledge.validation_rules:
            rule_result = self._check_validation_rule(df, rule)
            if rule_result:
                checks["business_rule_compliance"].append(rule_result)

        # Check for completeness of required fields
        for mapping in self.knowledge.column_mappings:
            if mapping.required:
                completeness = self._check_field_completeness(df, mapping.standard_name)
                checks["data_completeness"].append(completeness)

        return checks

    def _validate_s1_quality(self, df: pd.DataFrame) -> List[Dict]:
        """S1-specific quality validation: COA structure integrity."""
        validations = []

        # Finance code format validation
        if 'finance_code' in df.columns:
            invalid_codes = df[df['finance_code'].apply(
                lambda x: pd.notna(x) and (len(str(x)) != 4 or not str(x).isdigit())
            )]
            if len(invalid_codes) > 0:
                validations.append({
                    "check": "Finance Code Format",
                    "passed": False,
                    "severity": "critical",
                    "message": f"{len(invalid_codes)} finance codes not in 4-digit format",
                    "samples": invalid_codes['finance_code'].head(5).tolist()
                })
            else:
                validations.append({
                    "check": "Finance Code Format",
                    "passed": True,
                    "severity": "info",
                    "message": "All finance codes in valid 4-digit format"
                })

        # Cost centre validation
        if 'cost_centre' in df.columns:
            unique_cc = df['cost_centre'].dropna().unique()
            validations.append({
                "check": "Cost Centre Coverage",
                "passed": True,
                "severity": "info",
                "message": f"{len(unique_cc)} unique cost centres defined"
            })

        return validations

    def _validate_s2_quality(self, df: pd.DataFrame) -> List[Dict]:
        """S2-specific quality validation: Staff data integrity using S2 domain knowledge."""
        validations = []

        # =====================================================================
        # Staff member uniqueness
        # =====================================================================
        if 'payroll_number' in df.columns:
            duplicates = df['payroll_number'].dropna().duplicated().sum()
            if duplicates > 0:
                # Multiple rows per staff member is OK (multiple contracts)
                unique_staff = df['payroll_number'].dropna().nunique()
                total_rows = len(df[df['payroll_number'].notna()])
                validations.append({
                    "check": "Staff Data Structure",
                    "passed": True,
                    "severity": "info",
                    "message": f"{unique_staff} unique staff with {total_rows} contract rows"
                })
            else:
                validations.append({
                    "check": "Staff Data Structure",
                    "passed": True,
                    "severity": "info",
                    "message": "One row per staff member"
                })

        # =====================================================================
        # Pay Scale Validation using S2 Domain Knowledge
        # =====================================================================
        if S2_DOMAIN_KNOWLEDGE_AVAILABLE and 'pay_scale' in df.columns:
            # Validate against known pay scales from S2_PAY_SCALES
            pay_scales = df['pay_scale'].dropna().unique()
            valid_scales = set(S2_PAY_SCALES.keys())
            invalid_scales = [ps for ps in pay_scales if ps not in valid_scales]

            if invalid_scales:
                validations.append({
                    "check": "Pay Scale Codes (S2 Knowledge)",
                    "passed": False,
                    "severity": "warning",
                    "message": f"{len(invalid_scales)} unrecognized pay scale codes",
                    "samples": invalid_scales[:5],
                    "valid_scales": list(valid_scales)[:10]
                })
            else:
                validations.append({
                    "check": "Pay Scale Codes (S2 Knowledge)",
                    "passed": True,
                    "severity": "info",
                    "message": f"All {len(pay_scales)} pay scale codes are valid"
                })

        # Pay scale point format validation
        if 'current_scale_point' in df.columns:
            scale_points = df['current_scale_point'].dropna()
            valid_patterns = ['M', 'U', 'L', 'SCP']
            invalid_scales = scale_points[~scale_points.astype(str).str.upper().str.startswith(tuple(valid_patterns))]

            if len(invalid_scales) > 0:
                validations.append({
                    "check": "Pay Scale Point Format",
                    "passed": False,
                    "severity": "warning",
                    "message": f"{len(invalid_scales)} unrecognized pay scale point formats",
                    "samples": invalid_scales.head(5).tolist()
                })
            else:
                validations.append({
                    "check": "Pay Scale Point Format",
                    "passed": True,
                    "severity": "info",
                    "message": "All pay scale points in recognized format"
                })

        # =====================================================================
        # Staff Role Group Validation using S2 Domain Knowledge
        # =====================================================================
        if S2_DOMAIN_KNOWLEDGE_AVAILABLE and 'staff_role_group' in df.columns:
            role_groups = df['staff_role_group'].dropna().unique()
            valid_groups = set(STAFF_ROLE_GROUPS.keys())
            invalid_groups = [rg for rg in role_groups if rg not in valid_groups]

            if invalid_groups:
                validations.append({
                    "check": "Staff Role Groups (S2 Knowledge)",
                    "passed": False,
                    "severity": "warning",
                    "message": f"{len(invalid_groups)} unrecognized role group codes",
                    "samples": invalid_groups[:5],
                    "valid_groups": list(valid_groups)
                })
            else:
                validations.append({
                    "check": "Staff Role Groups (S2 Knowledge)",
                    "passed": True,
                    "severity": "info",
                    "message": f"All {len(role_groups)} role groups are valid"
                })

        # =====================================================================
        # Finance Code Derivation Check
        # =====================================================================
        if S2_DOMAIN_KNOWLEDGE_AVAILABLE:
            # Check if finance codes were properly derived
            if 'gross_salary_finance_code' in df.columns:
                missing_fc = (df['gross_salary_finance_code'].isna() | (df['gross_salary_finance_code'] == '')).sum()
                total = len(df)
                coverage = ((total - missing_fc) / total * 100) if total > 0 else 0

                if coverage < 80:
                    validations.append({
                        "check": "Finance Code Coverage",
                        "passed": False,
                        "severity": "warning",
                        "message": f"Only {coverage:.1f}% of records have finance codes derived",
                        "missing_count": missing_fc
                    })
                else:
                    validations.append({
                        "check": "Finance Code Coverage",
                        "passed": True,
                        "severity": "info",
                        "message": f"{coverage:.1f}% of records have finance codes ({total - missing_fc}/{total})"
                    })

        # =====================================================================
        # Equated Week Pattern Validation
        # =====================================================================
        if S2_DOMAIN_KNOWLEDGE_AVAILABLE and 'equated_week_pattern' in df.columns:
            patterns = df['equated_week_pattern'].dropna().unique()
            valid_patterns = set(EQUATED_WEEK_PATTERNS.keys())
            invalid_patterns = [p for p in patterns if p not in valid_patterns]

            if invalid_patterns:
                validations.append({
                    "check": "Equated Week Patterns (S2 Knowledge)",
                    "passed": False,
                    "severity": "warning",
                    "message": f"{len(invalid_patterns)} unrecognized equated week patterns",
                    "samples": invalid_patterns[:5]
                })
            else:
                validations.append({
                    "check": "Equated Week Patterns (S2 Knowledge)",
                    "passed": True,
                    "severity": "info",
                    "message": f"All equated week patterns are valid"
                })

        # =====================================================================
        # Combined Field Parsing Verification
        # =====================================================================
        if S2_DOMAIN_KNOWLEDGE_AVAILABLE:
            combined_cols = [c for c in df.columns if 'Combined' in str(c)]
            parsed_cols = [c for c in df.columns if c.endswith('_Code') or c.endswith('_Parsed')]

            if combined_cols and not parsed_cols:
                validations.append({
                    "check": "Combined Field Parsing",
                    "passed": False,
                    "severity": "error",
                    "message": f"{len(combined_cols)} combined fields found but not parsed",
                    "columns": combined_cols[:5]
                })
            elif combined_cols and parsed_cols:
                validations.append({
                    "check": "Combined Field Parsing",
                    "passed": True,
                    "severity": "info",
                    "message": f"{len(combined_cols)} combined fields parsed into {len(parsed_cols)} code columns"
                })

        # =====================================================================
        # Salary reasonableness check
        # =====================================================================
        if 'annual_salary' in df.columns:
            salaries = pd.to_numeric(df['annual_salary'], errors='coerce').dropna()
            if len(salaries) > 0:
                # Check for outliers
                min_sal = salaries.min()
                max_sal = salaries.max()
                median_sal = salaries.median()

                if min_sal < 10000:
                    validations.append({
                        "check": "Salary Range",
                        "passed": False,
                        "severity": "warning",
                        "message": f"Some salaries below £10,000 (min: £{min_sal:,.0f}) - verify if correct"
                    })
                elif max_sal > 200000:
                    validations.append({
                        "check": "Salary Range",
                        "passed": False,
                        "severity": "warning",
                        "message": f"Some salaries above £200,000 (max: £{max_sal:,.0f}) - verify if correct"
                    })
                else:
                    validations.append({
                        "check": "Salary Range",
                        "passed": True,
                        "severity": "info",
                        "message": f"Salary range £{min_sal:,.0f} - £{max_sal:,.0f} (median: £{median_sal:,.0f})"
                    })

        # =====================================================================
        # Validate salaries against EXTRACTED pay scales (if available)
        # =====================================================================
        if self.extracted_payscales and 'annual_salary' in df.columns and 'current_scale_point' in df.columns:
            # Build lookup of valid rates from extracted pay scales
            valid_rates = {}
            for ps in self.extracted_payscales:
                for point in ps.points:
                    valid_rates[point.code.upper()] = point.rate
                    # Also add variations
                    valid_rates[point.code] = point.rate
                    if point.original_code:
                        valid_rates[point.original_code.upper()] = point.rate

            # Check each staff member's salary against their scale point
            mismatches = []
            checked = 0
            for idx, row in df.iterrows():
                salary = pd.to_numeric(row.get('annual_salary'), errors='coerce')
                scale_point = str(row.get('current_scale_point', '')).upper().strip()

                if pd.notna(salary) and scale_point and scale_point in valid_rates:
                    checked += 1
                    expected_rate = valid_rates[scale_point]
                    # Allow 5% tolerance for FTE adjustments
                    if abs(salary - expected_rate) > expected_rate * 0.05:
                        mismatches.append({
                            "row": idx,
                            "scale_point": scale_point,
                            "actual_salary": salary,
                            "expected_rate": expected_rate,
                            "difference": salary - expected_rate
                        })

            if checked > 0:
                match_rate = ((checked - len(mismatches)) / checked) * 100
                validations.append({
                    "check": "Salary vs Extracted Pay Scale",
                    "passed": len(mismatches) == 0,
                    "severity": "warning" if mismatches else "info",
                    "message": f"{len(mismatches)} of {checked} checked salaries don't match extracted pay scale rates",
                    "match_rate": f"{match_rate:.1f}%",
                    "sample_mismatches": mismatches[:5] if mismatches else []
                })
            else:
                validations.append({
                    "check": "Salary vs Extracted Pay Scale",
                    "passed": True,
                    "severity": "info",
                    "message": "No salaries could be validated against extracted pay scales (scale points not matched)"
                })

        # =====================================================================
        # Teaching/Support Role-Pension Alignment
        # =====================================================================
        if 'role_type' in df.columns and 'pension_code' in df.columns:
            mismatched = df[
                ((df['role_type'] == 'teaching') & (~df['pension_code'].isin(['TPS', '0%', '']))) |
                ((df['role_type'] == 'support') & (~df['pension_code'].isin(['LGPS_IMP', '0%', ''])))
            ]
            if len(mismatched) > 0:
                validations.append({
                    "check": "Role-Pension Alignment",
                    "passed": False,
                    "severity": "warning",
                    "message": f"{len(mismatched)} records have role type / pension scheme mismatch",
                    "note": "Teaching should be TPS, Support should be LGPS"
                })
            else:
                validations.append({
                    "check": "Role-Pension Alignment",
                    "passed": True,
                    "severity": "info",
                    "message": "Role types and pension schemes are aligned"
                })

        return validations

    def _validate_s3_quality(self, df: pd.DataFrame) -> List[Dict]:
        """S3-specific quality validation: Financial data integrity."""
        validations = []

        # Budget balance check
        if 'amount' in df.columns:
            amounts = pd.to_numeric(df['amount'], errors='coerce').dropna()
            if len(amounts) > 0:
                total_income = amounts[amounts > 0].sum()
                total_expenditure = abs(amounts[amounts < 0].sum())
                balance = total_income - total_expenditure

                validations.append({
                    "check": "Budget Summary",
                    "passed": True,
                    "severity": "info",
                    "message": f"Income: £{total_income:,.0f}, Expenditure: £{total_expenditure:,.0f}, Balance: £{balance:,.0f}"
                })

                # Warning if large deficit
                if balance < -100000:
                    validations.append({
                        "check": "Budget Balance",
                        "passed": False,
                        "severity": "warning",
                        "message": f"Large projected deficit of £{abs(balance):,.0f} - verify figures"
                    })

        # Finance code presence
        if 'finance_code' in df.columns:
            missing_fc = df['finance_code'].isna().sum()
            total_rows = len(df)
            if missing_fc > 0:
                pct_missing = (missing_fc / total_rows) * 100
                validations.append({
                    "check": "Finance Code Coverage",
                    "passed": pct_missing < 10,
                    "severity": "warning" if pct_missing >= 10 else "info",
                    "message": f"{missing_fc} rows ({pct_missing:.1f}%) missing finance codes"
                })

        return validations

    def _check_validation_rule(self, df: pd.DataFrame, rule: str) -> Optional[Dict]:
        """Check a validation rule from knowledge base."""
        # Simple rule checking - could be expanded
        if "required" in rule.lower():
            return None  # Handled by completeness check
        return None

    def _check_field_completeness(self, df: pd.DataFrame, field_name: str) -> Dict:
        """Check completeness of a required field."""
        if field_name not in df.columns:
            return {
                "field": field_name,
                "present": False,
                "completeness": 0,
                "status": "missing"
            }

        non_null = df[field_name].notna().sum()
        total = len(df)
        completeness = (non_null / total * 100) if total > 0 else 0

        return {
            "field": field_name,
            "present": True,
            "completeness": round(completeness, 1),
            "status": "complete" if completeness >= 95 else "partial" if completeness >= 50 else "sparse"
        }

    def _update_quality_with_expert_findings(self, report: CheckInReport, expert_checks: Dict):
        """Update quality score based on expert findings."""
        expert_failures = 0
        expert_total = 0

        for category, checks in expert_checks.items():
            for check in checks:
                if isinstance(check, dict) and 'passed' in check:
                    expert_total += 1
                    if not check['passed']:
                        expert_failures += 1

        if expert_total > 0:
            expert_pass_rate = ((expert_total - expert_failures) / expert_total) * 100
            # Weight expert checks at 30% of final score
            original_score = report.details.get("quality_score", 0)
            adjusted_score = (original_score * 0.7) + (expert_pass_rate * 0.3)
            report.details["quality_score"] = round(adjusted_score, 1)
            report.details["expert_pass_rate"] = round(expert_pass_rate, 1)

    def _get_expert_recommendations(self, details: Dict) -> List[str]:
        """Get domain-specific recommendations."""
        recommendations = []

        expert_checks = details.get("expert_quality_checks", {})

        # Check for domain validation failures
        domain_validations = expert_checks.get("domain_validation", [])
        failed_domain = [v for v in domain_validations if isinstance(v, dict) and not v.get("passed", True)]

        if failed_domain:
            recommendations.append(f"Address {len(failed_domain)} domain-specific validation issues")

        # Check completeness
        completeness_checks = expert_checks.get("data_completeness", [])
        sparse_fields = [c for c in completeness_checks if isinstance(c, dict) and c.get("status") == "sparse"]

        if sparse_fields:
            field_names = [f["field"] for f in sparse_fields]
            recommendations.append(f"Review sparse required fields: {', '.join(field_names[:3])}")

        # Add knowledge-based guidance
        if self.knowledge.common_issues:
            recommendations.append(f"Verify against known issues: {self.knowledge.common_issues[0]}")

        return recommendations


class ExpertAuditorAgent(AuditorAgent):
    """Auditor agent with domain expertise for external review."""

    def __init__(self, team_id: str, team_config: Dict):
        super().__init__(team_id, team_config)
        self.knowledge = get_team_knowledge(team_id)

    def execute(self, input_data: Dict) -> CheckInReport:
        """Perform expert external review audit with domain knowledge."""
        self.log(f"Starting Expert External Audit for {self.knowledge.team_name}")

        # Run base audit
        report = super().execute(input_data)

        # Add expert audit checks based on team type
        expert_audit = self._perform_expert_audit(input_data)
        report.details["expert_audit"] = expert_audit

        # Update audit trail with expert findings
        if report.details.get("audit_trail"):
            report.details["audit_trail"].append({
                "timestamp": datetime.now().isoformat(),
                "action": "Expert Audit",
                "details": f"Performed domain-specific audit for {self.team_id}"
            })

        # Adjust accuracy score based on expert findings
        self._update_score_with_expert_findings(report, expert_audit)

        # Add expert recommendations
        expert_recs = self._get_expert_audit_recommendations(expert_audit)
        report.recommendations.extend(expert_recs)

        return report

    def _perform_expert_audit(self, input_data: Dict) -> Dict:
        """Perform domain-specific audit based on team type."""
        expert_results = {
            "domain_checks": [],
            "reference_data_validation": [],
            "business_rules_verification": [],
            "data_lineage": []
        }

        original_data = input_data.get("original_data")
        transformed_data = input_data.get("transformed_data")

        if transformed_data is None:
            return expert_results

        # Team-specific expert audit
        if self.team_id == "S1":
            expert_results.update(self._audit_s1_data(original_data, transformed_data))
        elif self.team_id == "S2":
            expert_results.update(self._audit_s2_data(original_data, transformed_data))
        elif self.team_id == "S3":
            expert_results.update(self._audit_s3_data(original_data, transformed_data))

        return expert_results

    def _audit_s1_data(self, original: pd.DataFrame, processed: pd.DataFrame) -> Dict:
        """S1-specific audit: Finance codes, schools, departments."""
        results = {"domain_checks": [], "reference_data_validation": []}

        # Check finance code format consistency
        fc_cols = [c for c in processed.columns if 'finance' in c.lower() or 'code' in c.lower()]
        for col in fc_cols:
            values = processed[col].dropna().astype(str)
            # Check for consistent format (e.g., all numeric or alphanumeric pattern)
            if len(values) > 0:
                numeric_count = values.str.match(r'^\d+$').sum()
                total_count = len(values)
                consistency = (numeric_count / total_count * 100) if total_count > 0 else 0

                results["domain_checks"].append({
                    "check": f"Finance Code Format: {col}",
                    "passed": consistency > 90 or consistency < 10,  # Should be consistently one type
                    "details": f"{consistency:.1f}% numeric format",
                    "severity": "info"
                })

        # Check school code uniqueness
        if 'school_code' in [c.lower() for c in processed.columns]:
            school_col = [c for c in processed.columns if 'school' in c.lower() and 'code' in c.lower()][0]
            duplicates = processed[school_col].dropna().duplicated().sum()
            results["reference_data_validation"].append({
                "check": "School Code Uniqueness",
                "passed": duplicates == 0,
                "details": f"{duplicates} duplicate school codes found",
                "severity": "warning" if duplicates > 0 else "info"
            })

        return results

    def _audit_s2_data(self, original: pd.DataFrame, processed: pd.DataFrame) -> Dict:
        """S2-specific audit: Staff, pay scales, contracts using S2 domain knowledge."""
        results = {"domain_checks": [], "reference_data_validation": [], "business_rules_verification": []}

        # Audit pay scale codes against known scales
        if S2_DOMAIN_KNOWLEDGE_AVAILABLE:
            pay_scale_cols = [c for c in processed.columns if 'pay' in c.lower() and 'scale' in c.lower()]
            for col in pay_scale_cols:
                values = processed[col].dropna().unique()
                unknown = [v for v in values if str(v) not in S2_PAY_SCALES]
                results["domain_checks"].append({
                    "check": f"Pay Scale Validation: {col}",
                    "passed": len(unknown) == 0,
                    "details": f"{len(unknown)} unknown pay scales: {unknown[:3]}",
                    "severity": "warning" if unknown else "info"
                })

            # Audit staff role groups
            role_cols = [c for c in processed.columns if 'role' in c.lower() and 'group' in c.lower()]
            for col in role_cols:
                values = processed[col].dropna().unique()
                unknown = [v for v in values if str(v) not in STAFF_ROLE_GROUPS]
                results["domain_checks"].append({
                    "check": f"Role Group Validation: {col}",
                    "passed": len(unknown) == 0,
                    "details": f"{len(unknown)} unknown role groups",
                    "severity": "warning" if unknown else "info"
                })

        # Verify teaching/support classification consistency
        if 'role_type' in processed.columns and 'pension_code' in processed.columns:
            teaching_staff = processed[processed['role_type'] == 'teaching']
            teaching_with_wrong_pension = teaching_staff[~teaching_staff['pension_code'].isin(['TPS', '0%', '', None])]

            results["business_rules_verification"].append({
                "check": "Teaching Staff Pension Rule",
                "passed": len(teaching_with_wrong_pension) == 0,
                "details": f"{len(teaching_with_wrong_pension)} teaching staff without TPS pension",
                "severity": "warning" if len(teaching_with_wrong_pension) > 0 else "info"
            })

        # Verify combined field parsing occurred
        combined_cols = [c for c in processed.columns if 'Combined' in str(c)]
        parsed_cols = [c for c in processed.columns if c.endswith('_Code') or c.endswith('_Parsed')]

        if combined_cols and not parsed_cols:
            results["domain_checks"].append({
                "check": "Combined Field Parsing",
                "passed": False,
                "details": f"{len(combined_cols)} combined fields not parsed",
                "severity": "warning"
            })
        elif parsed_cols:
            results["domain_checks"].append({
                "check": "Combined Field Parsing",
                "passed": True,
                "details": f"{len(parsed_cols)} code columns extracted",
                "severity": "info"
            })

        return results

    def _audit_s3_data(self, original: pd.DataFrame, processed: pd.DataFrame) -> Dict:
        """S3-specific audit: Financial data, budgets, pupils."""
        results = {"domain_checks": [], "reference_data_validation": [], "business_rules_verification": []}

        # Check for negative values in amount columns
        amount_cols = [c for c in processed.columns if any(x in c.lower() for x in ['amount', 'value', 'budget', 'pupil'])]
        for col in amount_cols:
            try:
                numeric_vals = pd.to_numeric(processed[col], errors='coerce').dropna()
                negative_count = (numeric_vals < 0).sum()

                if 'pupil' in col.lower():
                    # Pupil numbers should never be negative
                    results["business_rules_verification"].append({
                        "check": f"Pupil Numbers Non-Negative: {col}",
                        "passed": negative_count == 0,
                        "details": f"{negative_count} negative values found",
                        "severity": "critical" if negative_count > 0 else "info"
                    })
                else:
                    # Budget amounts can be negative (credits)
                    results["domain_checks"].append({
                        "check": f"Amount Values: {col}",
                        "passed": True,
                        "details": f"{negative_count} negative values (may be credits)",
                        "severity": "info"
                    })
            except Exception:
                continue

        # Check year columns are reasonable
        year_cols = [c for c in processed.columns if 'year' in c.lower()]
        current_year = datetime.now().year
        for col in year_cols:
            try:
                years = pd.to_numeric(processed[col], errors='coerce').dropna()
                future_years = (years > current_year + 10).sum()
                past_years = (years < current_year - 20).sum()

                if future_years > 0 or past_years > 0:
                    results["reference_data_validation"].append({
                        "check": f"Year Range: {col}",
                        "passed": False,
                        "details": f"{future_years} future, {past_years} historical values outside expected range",
                        "severity": "warning"
                    })
            except Exception:
                continue

        return results

    def _update_score_with_expert_findings(self, report: CheckInReport, expert_audit: Dict):
        """Update accuracy score based on expert findings."""
        expert_failures = 0
        expert_total = 0

        for category in ['domain_checks', 'reference_data_validation', 'business_rules_verification']:
            checks = expert_audit.get(category, [])
            for check in checks:
                if isinstance(check, dict) and 'passed' in check:
                    expert_total += 1
                    if not check['passed']:
                        expert_failures += 1

        if expert_total > 0:
            expert_pass_rate = ((expert_total - expert_failures) / expert_total) * 100
            original_score = report.details.get("accuracy_score", 0)
            # Weight expert audit at 25% of final score
            adjusted_score = (original_score * 0.75) + (expert_pass_rate * 0.25)
            report.details["accuracy_score"] = round(adjusted_score, 1)
            report.details["expert_audit_pass_rate"] = round(expert_pass_rate, 1)

    def _get_expert_audit_recommendations(self, expert_audit: Dict) -> List[str]:
        """Generate recommendations from expert audit findings."""
        recommendations = []

        # Check domain validation failures
        domain_checks = expert_audit.get("domain_checks", [])
        failed_domain = [c for c in domain_checks if isinstance(c, dict) and not c.get("passed", True)]

        if failed_domain:
            recommendations.append(f"EXPERT: Address {len(failed_domain)} domain-specific validation issues")

        # Check business rule violations
        business_checks = expert_audit.get("business_rules_verification", [])
        failed_business = [c for c in business_checks if isinstance(c, dict) and not c.get("passed", True)]

        if failed_business:
            recommendations.append(f"CRITICAL: {len(failed_business)} business rule violations detected")

        # Check reference data issues
        ref_checks = expert_audit.get("reference_data_validation", [])
        failed_ref = [c for c in ref_checks if isinstance(c, dict) and not c.get("passed", True)]

        if failed_ref:
            recommendations.append(f"VERIFY: {len(failed_ref)} reference data inconsistencies found")

        if not (failed_domain or failed_business or failed_ref):
            recommendations.append("EXPERT AUDIT PASSED: All domain-specific checks passed")

        return recommendations


class ExpertAgentTeam(AgentTeam):
    """Agent team with expert knowledge."""

    def __init__(self, team_id: str, team_config: Dict, template_path: Path):
        self.team_id = team_id
        self.team_config = team_config
        self.template_path = template_path
        self.knowledge = get_team_knowledge(team_id)

        # Create EXPERT agents for each phase
        self.agents = {
            "analyze": ExpertAnalyzeAgent(team_id, team_config),
            "clean": ExpertCleanAgent(team_id, team_config),
            "transform": ExpertTransformAgent(team_id, team_config),
            "build": ExpertBuildAgent(team_id, team_config, template_path),
            "quality_check": ExpertQualityCheckAgent(team_id, team_config),
            "audit": ExpertAuditorAgent(team_id, team_config)
        }

        self.reports = []
        self.current_phase = ""
        self.phase_data = {}
        self.all_assumptions = []

        self.log(f"Initialized {self.knowledge.team_name} with expert knowledge")
        self.log(f"Focus: {self.knowledge.description}")

    def log(self, message: str):
        """Log a message."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{self.team_id}:EXPERT] {message}")

    @property
    def name(self) -> str:
        return f"{self.knowledge.team_name} (Expert)"

    def get_knowledge_summary(self) -> Dict:
        """Get summary of team's knowledge."""
        return {
            "team": self.knowledge.team_name,
            "key_concepts": list(self.knowledge.key_concepts.keys()),
            "column_mappings": len(self.knowledge.column_mappings),
            "validation_rules": len(self.knowledge.validation_rules),
            "business_rules": len(self.knowledge.business_rules),
            "common_issues": self.knowledge.common_issues[:5]
        }

    def get_inference_stats(self) -> Optional[Dict]:
        """
        Get statistics from the InferenceEngine.

        Returns stats about rules, schemas, learning, and decisions made.
        """
        engine = get_inference_engine()
        if engine:
            return engine.get_stats()
        return None

    def get_reasoning_trails(self) -> Optional[Dict]:
        """
        Get all reasoning trails from the InferenceEngine.

        Returns full audit trail of all decisions for review.
        """
        engine = get_inference_engine()
        if engine:
            return engine.get_all_reasoning_trails()
        return None

    def get_warnings_and_assumptions(self) -> Dict:
        """
        Get all warnings and assumptions from inference decisions.

        Useful for post-processing review of low-confidence decisions.
        """
        engine = get_inference_engine()
        if engine:
            return {
                "warnings": engine.get_warnings(),
                "assumptions": engine.get_assumptions()
            }
        return {"warnings": [], "assumptions": []}

    def run_all(self, check_in_callback=None) -> List[CheckInReport]:
        """
        Run all phases with expert knowledge sharing between phases.

        For S2 team: Extracted pay scales from analyze phase are passed to
        quality_check and audit phases for validation.
        """
        phases = ["analyze", "clean", "transform", "build", "quality_check", "audit"]

        # Storage for S2 pay scale extraction
        extracted_payscales = None
        extracted_allowances = None

        for phase in phases:
            # Determine input for this phase
            if phase == "analyze":
                input_data = self.team_config['data_dir']
            elif phase == "quality_check":
                # QA agent gets all accumulated data from previous phases
                input_data = self.phase_data.get("build", {})
                # S2 SPECIFIC: Pass extracted pay scales for validation
                if self.team_id == "S2" and extracted_payscales:
                    input_data["extracted_payscales"] = extracted_payscales
                    input_data["extracted_allowances"] = extracted_allowances
            elif phase == "audit":
                # Auditor gets both original and transformed data for comparison
                input_data = {
                    "original_data": self.phase_data.get("analyze", {}).get("data"),
                    "transformed_data": self.phase_data.get("transform", {}).get("data"),
                    "output_path": self.phase_data.get("build", {}).get("output_path", ""),
                    "source_files": self.phase_data.get("analyze", {}).get("source_files", [])
                }
                # S2 SPECIFIC: Pass extracted pay scales for audit
                if self.team_id == "S2" and extracted_payscales:
                    input_data["extracted_payscales"] = extracted_payscales
                    input_data["extracted_allowances"] = extracted_allowances
            else:
                prev_phase = phases[phases.index(phase) - 1]
                input_data = self.phase_data.get(prev_phase, {})

            report = self.run_phase(phase, input_data)

            # S2 SPECIFIC: Capture extracted pay scales after analyze phase
            if phase == "analyze" and self.team_id == "S2":
                analyze_agent = self.agents["analyze"]
                if hasattr(analyze_agent, 'extracted_payscales') and analyze_agent.extracted_payscales:
                    extracted_payscales = analyze_agent.extracted_payscales
                    extracted_allowances = analyze_agent.extracted_allowances
                    self.log(f"Captured {len(extracted_payscales)} pay scales for downstream validation")

                    # Log pay scale extraction status
                    if report.details.get("payscale_extraction", {}).get("status") == "warning":
                        self.log("WARNING: Pay scale extraction completed with warnings")
                    elif report.details.get("payscale_extraction", {}).get("status") == "success":
                        self.log("Pay scale extraction successful")

            # Call check-in callback if provided
            if check_in_callback:
                check_in_callback(report)

        return self.reports
