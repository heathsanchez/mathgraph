"""SQLite-backed persistent memory for verified MathGraph lawbook traces."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Iterator
from typing import Any

from mathgraph.lawbook import CertificateLawbook
from mathgraph.trace import Trace


@dataclass(frozen=True)
class LawbookStoreStats:
    trace_count: int
    claim_count: int
    certificate_count: int
    pair_count: int
    source_count: int
    target_count: int
    route_counts: dict[str, int]
    terminal_form_counts: dict[str, int]
    verification_status_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_count": self.trace_count,
            "claim_count": self.claim_count,
            "certificate_count": self.certificate_count,
            "pair_count": self.pair_count,
            "source_count": self.source_count,
            "target_count": self.target_count,
            "route_counts": dict(self.route_counts),
            "terminal_form_counts": dict(self.terminal_form_counts),
            "verification_status_counts": dict(self.verification_status_counts),
        }


class LawbookStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row

    def init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim TEXT NOT NULL,
                claim_hash TEXT,
                source TEXT,
                target TEXT,
                source_idx TEXT,
                target_idx TEXT,
                compiled_route TEXT,
                terminal_form TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                promotion_status TEXT,
                lean_status TEXT,
                certificate_id TEXT,
                certificate_payload_keys_json TEXT NOT NULL,
                metadata_keys_json TEXT NOT NULL,
                trace_json TEXT NOT NULL,
                certificate_json TEXT,
                metadata_json TEXT NOT NULL,
                created TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_traces_claim ON traces(claim);
            CREATE INDEX IF NOT EXISTS idx_traces_claim_hash ON traces(claim_hash);
            CREATE INDEX IF NOT EXISTS idx_traces_source ON traces(source);
            CREATE INDEX IF NOT EXISTS idx_traces_target ON traces(target);
            CREATE INDEX IF NOT EXISTS idx_traces_pair ON traces(source, target);
            CREATE INDEX IF NOT EXISTS idx_traces_idx_pair ON traces(source_idx, target_idx);
            CREATE INDEX IF NOT EXISTS idx_traces_source_idx ON traces(source_idx);
            CREATE INDEX IF NOT EXISTS idx_traces_target_idx ON traces(target_idx);
            CREATE INDEX IF NOT EXISTS idx_traces_route ON traces(compiled_route);
            CREATE INDEX IF NOT EXISTS idx_traces_terminal ON traces(terminal_form);
            CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(verification_status);

            CREATE TABLE IF NOT EXISTS derived_certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                derived_claim TEXT NOT NULL,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                source_idx TEXT,
                target_idx TEXT,
                terminal_form TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                derivation_rule TEXT NOT NULL,
                trust_level TEXT NOT NULL,
                parent_claims_json TEXT NOT NULL,
                parent_pairs_json TEXT NOT NULL,
                route TEXT NOT NULL,
                explanation TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                warnings_json TEXT NOT NULL,
                created_ts TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_derived_pair ON derived_certificates(source, target);
            CREATE INDEX IF NOT EXISTS idx_derived_terminal ON derived_certificates(terminal_form);
            CREATE INDEX IF NOT EXISTS idx_derived_rule ON derived_certificates(derivation_rule);
            CREATE INDEX IF NOT EXISTS idx_derived_trust ON derived_certificates(trust_level);

            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                domain TEXT,
                source TEXT,
                target TEXT,
                normalized_source TEXT,
                normalized_target TEXT,
                source_idx TEXT,
                target_idx TEXT,
                claim_type TEXT,
                terminal_form TEXT,
                verification_status TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                metadata_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_claims_pair_idx ON claims(source_idx, target_idx);
            CREATE INDEX IF NOT EXISTS idx_claims_pair_text ON claims(normalized_source, normalized_target);
            CREATE INDEX IF NOT EXISTS idx_claims_terminal ON claims(terminal_form);

            CREATE TABLE IF NOT EXISTS certificates (
                certificate_id TEXT PRIMARY KEY,
                claim_id TEXT,
                source_idx TEXT,
                target_idx TEXT,
                terminal_form TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                trust_level TEXT,
                provenance_type TEXT,
                derivation_rule TEXT,
                route TEXT,
                payload_json TEXT NOT NULL,
                evidence_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_certificates_claim ON certificates(claim_id);
            CREATE INDEX IF NOT EXISTS idx_certificates_pair_idx ON certificates(source_idx, target_idx);
            CREATE INDEX IF NOT EXISTS idx_certificates_terminal ON certificates(terminal_form);

            CREATE TABLE IF NOT EXISTS refutations (
                refutation_id TEXT PRIMARY KEY,
                claim_id TEXT,
                source TEXT,
                target TEXT,
                source_idx TEXT,
                target_idx TEXT,
                terminal_form TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                trust_level TEXT,
                provenance_type TEXT,
                table_hash TEXT,
                table_name TEXT,
                table_json TEXT,
                witness_json TEXT,
                derivation_rule TEXT,
                elevation_method TEXT,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_refutations_pair_idx ON refutations(source_idx, target_idx);
            CREATE INDEX IF NOT EXISTS idx_refutations_pair_text ON refutations(source, target);
            CREATE INDEX IF NOT EXISTS idx_refutations_table_hash ON refutations(table_hash);

            CREATE TABLE IF NOT EXISTS certificate_edges (
                edge_id TEXT PRIMARY KEY,
                parent_certificate_id TEXT,
                child_certificate_id TEXT,
                edge_type TEXT,
                evidence_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS roots (
                root_node_id TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                root_type TEXT,
                root_key TEXT,
                table_motif TEXT,
                algebra_shape TEXT,
                source_target_basin TEXT,
                forced_transition TEXT,
                support_count INTEGER,
                rows INTEGER,
                unique_pairs INTEGER,
                unique_sources INTEGER,
                unique_targets INTEGER,
                unique_tables INTEGER,
                unique_motifs INTEGER,
                load_bearing_score REAL,
                status TEXT,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_roots_score ON roots(load_bearing_score);
            CREATE INDEX IF NOT EXISTS idx_roots_motif ON roots(table_motif);

            CREATE TABLE IF NOT EXISTS root_aliases (
                alias TEXT PRIMARY KEY,
                root_node_id TEXT,
                canonical_name TEXT,
                evidence_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reasons (
                reason_node_id TEXT PRIMARY KEY,
                reason_type TEXT,
                reason_key TEXT,
                table_motif TEXT,
                algebra_shape TEXT,
                forced_transition TEXT,
                derivation_rule TEXT,
                support_count INTEGER,
                rows INTEGER,
                reason_score REAL,
                status TEXT,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_reasons_score ON reasons(reason_score);

            CREATE TABLE IF NOT EXISTS obstructions (
                obstruction_id TEXT PRIMARY KEY,
                obstruction_signature TEXT,
                failure_reason TEXT,
                derivation_rule TEXT,
                source_target_basin TEXT,
                forced_transition TEXT,
                table_motif TEXT,
                rows INTEGER,
                obstruction_pressure_score REAL,
                payload_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_obstructions_pressure ON obstructions(obstruction_pressure_score);

            CREATE TABLE IF NOT EXISTS tables (
                table_hash TEXT PRIMARY KEY,
                table_name TEXT,
                table_json TEXT,
                motif TEXT,
                algebra_shape TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS artifact_imports (
                import_id TEXT PRIMARY KEY,
                artifact_path TEXT,
                artifact_kind TEXT,
                row_count INTEGER,
                status TEXT,
                warnings_json TEXT NOT NULL,
                created_ts TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS domain_kernels (
                kernel_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                native_language TEXT,
                host_verifier TEXT NOT NULL,
                embedding_kind TEXT NOT NULL,
                source_uri TEXT,
                source_commit TEXT,
                trust_policy TEXT,
                ontology_summary_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_domain_kernels_name ON domain_kernels(name);
            CREATE INDEX IF NOT EXISTS idx_domain_kernels_host ON domain_kernels(host_verifier);

            CREATE TABLE IF NOT EXISTS semantic_embeddings (
                embedding_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT NOT NULL,
                source_logic TEXT,
                target_logic TEXT,
                host_verifier TEXT,
                embedding_kind TEXT,
                description TEXT,
                soundness_status TEXT,
                artifact_uri TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_embeddings_kernel ON semantic_embeddings(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS imported_theory_objects (
                object_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                name TEXT,
                statement TEXT,
                source_file TEXT,
                source_line INTEGER,
                trust_level TEXT,
                provenance_type TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_theory_objects_kernel ON imported_theory_objects(domain_kernel_id);
            CREATE INDEX IF NOT EXISTS idx_theory_objects_kind ON imported_theory_objects(kind);

            CREATE TABLE IF NOT EXISTS imported_theory_relations (
                relation_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT NOT NULL,
                source_object_id TEXT,
                target_object_id TEXT,
                relation_kind TEXT NOT NULL,
                trust_level TEXT,
                provenance_type TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_theory_relations_kernel ON imported_theory_relations(domain_kernel_id);
            CREATE INDEX IF NOT EXISTS idx_theory_relations_source ON imported_theory_relations(source_object_id);

            CREATE TABLE IF NOT EXISTS typed_objects (
                object_id TEXT PRIMARY KEY,
                type_expr TEXT NOT NULL,
                object_kind TEXT NOT NULL,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                ordinary_or_abstract TEXT,
                identity_mode TEXT,
                uniqueness_status TEXT,
                hyperintensional_identity_mode TEXT,
                label TEXT,
                encoded_properties_json TEXT NOT NULL,
                exemplified_properties_json TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_typed_objects_kernel ON typed_objects(domain_kernel_id);
            CREATE INDEX IF NOT EXISTS idx_typed_objects_world ON typed_objects(formal_world_id);
            CREATE INDEX IF NOT EXISTS idx_typed_objects_kind ON typed_objects(object_kind);

            CREATE TABLE IF NOT EXISTS predication_facts (
                predication_id TEXT PRIMARY KEY,
                subject_id TEXT NOT NULL,
                predicate_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                predicate_kind TEXT,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                denotation_status TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_predication_subject ON predication_facts(subject_id);
            CREATE INDEX IF NOT EXISTS idx_predication_mode ON predication_facts(mode);
            CREATE INDEX IF NOT EXISTS idx_predication_kernel ON predication_facts(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS denotation_records (
                denotation_id TEXT PRIMARY KEY,
                object_id TEXT NOT NULL,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                denotation_status TEXT NOT NULL,
                reason TEXT,
                checked_by TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_denotation_object ON denotation_records(object_id);
            CREATE INDEX IF NOT EXISTS idx_denotation_kernel ON denotation_records(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS language_fragments (
                fragment_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                language_name TEXT,
                width_bound INTEGER,
                height_bound INTEGER,
                supported_type_exprs_json TEXT NOT NULL,
                supported_term_constructors_json TEXT NOT NULL,
                supported_claim_types_json TEXT NOT NULL,
                supported_verifiers_json TEXT NOT NULL,
                blocked_term_patterns_json TEXT NOT NULL,
                paradox_guard_policy TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_language_fragments_kernel ON language_fragments(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS theory_objectification_maps (
                map_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                theory_id TEXT,
                description TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_objectification_maps_kernel ON theory_objectification_maps(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS theory_denotations (
                denotation_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                theory_id TEXT,
                source_symbol TEXT,
                source_kind TEXT,
                target_object_id TEXT,
                target_type_expr TEXT,
                denotation_status TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_theory_denotations_kernel ON theory_denotations(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS theory_readings (
                reading_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                theory_id TEXT,
                source_statement TEXT,
                reading_statement TEXT,
                reading_type_expr TEXT,
                denotation_status TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_theory_readings_kernel ON theory_readings(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS analytic_truths (
                analytic_truth_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                theory_id TEXT,
                statement TEXT,
                reading_id TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                verifier_id TEXT,
                denotation_status TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_analytic_truths_kernel ON analytic_truths(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS formal_worlds (
                formal_world_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                name TEXT,
                world_kind TEXT,
                object_logic TEXT,
                identity_policy TEXT,
                denotation_policy TEXT,
                verifier_policy TEXT,
                language_fragment_ids_json TEXT NOT NULL,
                semantic_embedding_ids_json TEXT NOT NULL,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_formal_worlds_kernel ON formal_worlds(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS paradox_guards (
                guard_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                guard_kind TEXT,
                name TEXT,
                description TEXT,
                severity TEXT,
                blocked_patterns_json TEXT NOT NULL,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_paradox_guards_kernel ON paradox_guards(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS reason_containment_records (
                containment_id TEXT PRIMARY KEY,
                reason_node_id TEXT,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                source_id TEXT,
                target_id TEXT,
                containment_mode TEXT,
                source_constraints TEXT,
                target_demand TEXT,
                separator_certificate_id TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                denotation_status TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_reason_containment_reason ON reason_containment_records(reason_node_id);

            CREATE TABLE IF NOT EXISTS object_language_terms (
                term_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                raw_text TEXT,
                normalized_text TEXT,
                type_expr TEXT,
                denotation_status TEXT,
                role TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_object_terms_kernel ON object_language_terms(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS object_language_formulas (
                formula_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                raw_text TEXT,
                normalized_text TEXT,
                type_expr TEXT,
                formula_role TEXT,
                denotation_status TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_object_formulas_kernel ON object_language_formulas(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS theory_declarations (
                declaration_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                theory_id TEXT,
                declaration_kind TEXT,
                name TEXT,
                statement TEXT,
                source_file TEXT,
                source_line INTEGER,
                trust_level TEXT,
                provenance_type TEXT,
                host_logic TEXT,
                object_logic TEXT,
                object_theory_verified INTEGER,
                host_embedding_verified INTEGER,
                artifact_risk TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_theory_declarations_kernel ON theory_declarations(domain_kernel_id);
            CREATE INDEX IF NOT EXISTS idx_theory_declarations_kind ON theory_declarations(declaration_kind);

            CREATE TABLE IF NOT EXISTS proof_methods (
                proof_method_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                theory_id TEXT,
                name TEXT,
                method_kind TEXT,
                source_file TEXT,
                source_line INTEGER,
                trust_level TEXT,
                provenance_type TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_proof_methods_kernel ON proof_methods(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS inference_rules (
                inference_rule_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                theory_id TEXT,
                name TEXT,
                rule_kind TEXT,
                statement TEXT,
                source_file TEXT,
                source_line INTEGER,
                trust_level TEXT,
                provenance_type TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_inference_rules_kernel ON inference_rules(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS isabelle_export_records (
                export_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                theory_id TEXT,
                name TEXT,
                source_file TEXT,
                host_logic TEXT,
                object_logic TEXT,
                export_status TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_isabelle_exports_kernel ON isabelle_export_records(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS host_object_theorem_links (
                link_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                theory_id TEXT,
                host_theorem_id TEXT,
                object_theorem_id TEXT,
                export_status TEXT,
                proof_transport_status TEXT,
                artifact_risk TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_host_object_links_kernel ON host_object_theorem_links(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS logical_workbenches (
                workbench_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                layer TEXT,
                domain_kernel_ids_json TEXT NOT NULL,
                formal_world_ids_json TEXT NOT NULL,
                logic_combination_ids_json TEXT NOT NULL,
                benchmark_suite_ids_json TEXT NOT NULL,
                lifecycle_status TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_logical_workbenches_layer ON logical_workbenches(layer);

            CREATE TABLE IF NOT EXISTS embedding_strategy_profiles (
                profile_id TEXT PRIMARY KEY,
                embedding_id TEXT,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                strategy TEXT,
                syntax_representation TEXT,
                semantics_representation TEXT,
                automation_bias TEXT,
                expected_strengths_json TEXT NOT NULL,
                expected_risks_json TEXT NOT NULL,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_embedding_profiles_kernel ON embedding_strategy_profiles(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS faithfulness_assessments (
                assessment_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                embedding_id TEXT,
                object_logic TEXT,
                host_logic TEXT,
                status TEXT,
                soundness_status TEXT,
                completeness_status TEXT,
                benchmark_suite_id TEXT,
                proof_artifact_id TEXT,
                counterexamples_found INTEGER,
                assessed_by TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_faithfulness_kernel ON faithfulness_assessments(domain_kernel_id);
            CREATE INDEX IF NOT EXISTS idx_faithfulness_embedding ON faithfulness_assessments(embedding_id);

            CREATE TABLE IF NOT EXISTS logic_combinations (
                combination_id TEXT PRIMARY KEY,
                name TEXT,
                component_kernel_ids_json TEXT NOT NULL,
                component_formal_world_ids_json TEXT NOT NULL,
                combination_method TEXT,
                shared_semantic_domains_json TEXT NOT NULL,
                interaction_axioms_json TEXT NOT NULL,
                conflict_policy TEXT,
                faithfulness_status TEXT,
                benchmark_status TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS verifier_backend_profiles (
                backend_id TEXT PRIMARY KEY,
                name TEXT,
                backend_kind TEXT,
                roles_json TEXT NOT NULL,
                host_logic TEXT,
                object_logic TEXT,
                supports_proofs INTEGER,
                supports_models INTEGER,
                produces_replayable_artifacts INTEGER,
                native_to_domain_kernel INTEGER,
                artifact_risk TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_backend_kind ON verifier_backend_profiles(backend_kind);

            CREATE TABLE IF NOT EXISTS proof_finder_results (
                result_id TEXT PRIMARY KEY,
                claim_id TEXT,
                backend_id TEXT,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                status TEXT,
                proof_artifact_id TEXT,
                proof_text TEXT,
                runtime_sec REAL,
                trust_level TEXT,
                provenance_type TEXT,
                artifact_risk TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_proof_results_claim ON proof_finder_results(claim_id);

            CREATE TABLE IF NOT EXISTS model_finder_results (
                result_id TEXT PRIMARY KEY,
                claim_id TEXT,
                backend_id TEXT,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                status TEXT,
                model_artifact_id TEXT,
                model_payload_json TEXT NOT NULL,
                scope_bounds_json TEXT NOT NULL,
                runtime_sec REAL,
                trust_level TEXT,
                provenance_type TEXT,
                artifact_risk TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_model_results_claim ON model_finder_results(claim_id);

            CREATE TABLE IF NOT EXISTS benchmark_suites (
                suite_id TEXT PRIMARY KEY,
                name TEXT,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                description TEXT,
                case_count INTEGER,
                source TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_benchmark_suites_kernel ON benchmark_suites(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS benchmark_cases (
                case_id TEXT PRIMARY KEY,
                suite_id TEXT,
                claim_id TEXT,
                source_statement TEXT,
                target_statement TEXT,
                expected_status TEXT,
                expected_terminal_form TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_benchmark_cases_suite ON benchmark_cases(suite_id);

            CREATE TABLE IF NOT EXISTS benchmark_runs (
                run_id TEXT PRIMARY KEY,
                suite_id TEXT,
                backend_id TEXT,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                started_at TEXT,
                finished_at TEXT,
                total_cases INTEGER,
                passed_cases INTEGER,
                failed_cases INTEGER,
                unknown_cases INTEGER,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_benchmark_runs_suite ON benchmark_runs(suite_id);

            CREATE TABLE IF NOT EXISTS benchmark_results (
                result_id TEXT PRIMARY KEY,
                run_id TEXT,
                case_id TEXT,
                observed_status TEXT,
                expected_status TEXT,
                verifier_backend_id TEXT,
                runtime_sec REAL,
                proof_result_id TEXT,
                model_result_id TEXT,
                artifact_risk TEXT,
                regression_status TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_benchmark_results_run ON benchmark_results(run_id);

            CREATE TABLE IF NOT EXISTS correspondence_claims (
                correspondence_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                semantic_condition_id TEXT,
                syntactic_axiom_id TEXT,
                source_object_id TEXT,
                target_object_id TEXT,
                direction TEXT,
                status TEXT,
                proof_artifact_id TEXT,
                countermodel_artifact_id TEXT,
                benchmark_suite_id TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_correspondence_kernel ON correspondence_claims(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS interpretation_choice_points (
                choice_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                ambiguous_symbol TEXT,
                context TEXT,
                candidate_readings_json TEXT NOT NULL,
                selected_reading_id TEXT,
                rejected_reading_ids_json TEXT NOT NULL,
                downstream_effects_json TEXT NOT NULL,
                status TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                notes TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_interpretation_choices_kernel ON interpretation_choice_points(domain_kernel_id);

            CREATE TABLE IF NOT EXISTS proof_motifs (
                proof_motif_id TEXT PRIMARY KEY,
                motif_kind TEXT,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                source_basin TEXT,
                target_basin TEXT,
                source_shape TEXT,
                target_shape TEXT,
                route_signature TEXT,
                normalized_pattern TEXT,
                support_count INTEGER,
                unique_sources INTEGER,
                unique_targets INTEGER,
                unique_claims INTEGER,
                example_claim_ids_json TEXT NOT NULL,
                example_source_idxs_json TEXT NOT NULL,
                example_target_idxs_json TEXT NOT NULL,
                trust_level TEXT,
                provenance_type TEXT,
                verification_status TEXT,
                status TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_proof_motifs_kind ON proof_motifs(motif_kind);
            CREATE INDEX IF NOT EXISTS idx_proof_motifs_support ON proof_motifs(support_count);

            CREATE TABLE IF NOT EXISTS lemma_candidates (
                lemma_candidate_id TEXT PRIMARY KEY,
                candidate_name TEXT,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                proof_motif_id TEXT,
                reason_node_id TEXT,
                root_node_id TEXT,
                cut_kind TEXT,
                statement_text TEXT,
                normalized_statement TEXT,
                lean_statement TEXT,
                lean_sketch TEXT,
                expected_covered_claims INTEGER,
                example_claim_ids_json TEXT NOT NULL,
                example_source_idxs_json TEXT NOT NULL,
                example_target_idxs_json TEXT NOT NULL,
                status TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                verification_status TEXT,
                verifier_id TEXT,
                proof_artifact_id TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_lemma_candidates_status ON lemma_candidates(status);
            CREATE INDEX IF NOT EXISTS idx_lemma_candidates_coverage ON lemma_candidates(expected_covered_claims);

            CREATE TABLE IF NOT EXISTS lean_artifacts (
                lean_artifact_id TEXT PRIMARY KEY,
                artifact_kind TEXT,
                name TEXT,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                theorem_name TEXT,
                statement TEXT,
                proof_text TEXT,
                imports_json TEXT NOT NULL,
                depends_on_json TEXT NOT NULL,
                verification_status TEXT,
                trust_level TEXT,
                provenance_type TEXT,
                source_file TEXT,
                line_start INTEGER,
                line_end INTEGER,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_lean_artifacts_status ON lean_artifacts(verification_status);
            CREATE INDEX IF NOT EXISTS idx_lean_artifacts_kind ON lean_artifacts(artifact_kind);

            CREATE TABLE IF NOT EXISTS proof_atlases (
                atlas_id TEXT PRIMARY KEY,
                domain_kernel_id TEXT,
                formal_world_id TEXT,
                proof_motif_ids_json TEXT NOT NULL,
                lemma_candidate_ids_json TEXT NOT NULL,
                lean_artifact_ids_json TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_proof_atlases_kernel ON proof_atlases(domain_kernel_id);
            """
        )
        self._ensure_columns(
            "domain_kernels",
            {
                "host_logic": "TEXT",
                "object_logic": "TEXT",
                "object_theory": "TEXT",
                "artifact_risk": "TEXT",
                "proof_transport_status": "TEXT",
                "default_denotation_policy": "TEXT",
                "default_type_system": "TEXT",
                "default_identity_policy": "TEXT",
                "default_hyperintensional_identity_policy": "TEXT",
                "extensional_collapse_policy": "TEXT",
                "workbench_id": "TEXT",
                "workbench_layer": "TEXT",
                "lifecycle_status": "TEXT",
                "embedding_strategy": "TEXT",
                "faithfulness_status": "TEXT",
                "benchmark_status": "TEXT",
                "default_formal_world_id": "TEXT",
                "notes": "TEXT",
            },
        )
        self._ensure_columns(
            "semantic_embeddings",
            {
                "formal_world_id": "TEXT",
                "host_logic": "TEXT",
                "object_logic": "TEXT",
                "object_theory": "TEXT",
                "artifact_risk": "TEXT",
                "object_theory_verified": "INTEGER",
                "host_embedding_verified": "INTEGER",
                "proof_transport_status": "TEXT",
                "embedding_strategy_profile_id": "TEXT",
                "faithfulness_assessment_id": "TEXT",
                "syntax_representation": "TEXT",
                "semantics_representation": "TEXT",
                "automation_bias": "TEXT",
                "notes": "TEXT",
                "payload_json": "TEXT",
            },
        )
        self._ensure_columns(
            "formal_worlds",
            {
                "workbench_id": "TEXT",
                "lifecycle_status": "TEXT",
                "embedding_strategy_profile_ids_json": "TEXT",
                "faithfulness_assessment_ids_json": "TEXT",
                "benchmark_suite_ids_json": "TEXT",
                "verifier_backend_ids_json": "TEXT",
                "logic_combination_ids_json": "TEXT",
                "interpretation_choice_ids_json": "TEXT",
            },
        )
        self.conn.commit()

    def _ensure_columns(self, table: str, columns: dict[str, str]) -> None:
        existing = {
            str(row["name"])
            for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for name, spec in columns.items():
            if name not in existing:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {spec}")

    def close(self) -> None:
        self.conn.close()

    def import_traces_json(self, path: str | Path, replace: bool = False) -> LawbookStoreStats:
        return self.import_lawbook(CertificateLawbook.from_json(path), replace=replace)

    def import_lawbook(self, lawbook: CertificateLawbook, replace: bool = False) -> LawbookStoreStats:
        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM traces")
        rows = [_trace_row(trace) for trace in lawbook.traces]
        self.conn.executemany(
            """
            INSERT INTO traces (
                claim, claim_hash, source, target, source_idx, target_idx,
                compiled_route, terminal_form, verification_status, promotion_status,
                lean_status, certificate_id, certificate_payload_keys_json,
                metadata_keys_json, trace_json, certificate_json, metadata_json, created
            ) VALUES (
                :claim, :claim_hash, :source, :target, :source_idx, :target_idx,
                :compiled_route, :terminal_form, :verification_status, :promotion_status,
                :lean_status, :certificate_id, :certificate_payload_keys_json,
                :metadata_keys_json, :trace_json, :certificate_json, :metadata_json, :created
            )
            """,
            rows,
        )
        self.conn.commit()
        return self.stats()

    def import_derived_certificates(
        self, certificates: list["DerivedCertificate"], replace: bool = False
    ) -> "DerivedCertificateStats":
        from mathgraph.derived_certificates import DerivedCertificateStats

        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM derived_certificates")
        rows = [_derived_row(cert) for cert in certificates]
        self.conn.executemany(
            """
            INSERT INTO derived_certificates (
                derived_claim, source, target, source_idx, target_idx,
                terminal_form, verification_status, derivation_rule, trust_level,
                parent_claims_json, parent_pairs_json, route, explanation,
                evidence_json, warnings_json, created_ts
            ) VALUES (
                :derived_claim, :source, :target, :source_idx, :target_idx,
                :terminal_form, :verification_status, :derivation_rule, :trust_level,
                :parent_claims_json, :parent_pairs_json, :route, :explanation,
                :evidence_json, :warnings_json, :created_ts
            )
            """,
            rows,
        )
        self.conn.commit()
        stats = self.derived_stats()
        return DerivedCertificateStats(
            input_trace_count=self.stats().trace_count,
            input_true_count=self.stats().terminal_form_counts.get("VERIFIED_PROOF", 0),
            input_false_count=self.stats().terminal_form_counts.get("FINITE_COUNTERMODEL", 0),
            derived_true_count=stats["terminal_form_counts"].get("VERIFIED_PROOF", 0),
            derived_false_count=stats["terminal_form_counts"].get("FINITE_COUNTERMODEL", 0),
            duplicate_skipped_count=0,
            malformed_skipped_count=0,
            total_derived_count=stats["total"],
            rule_counts=stats["rule_counts"],
        )

    def import_claims(self, claims: list[Any], replace: bool = False) -> dict[str, Any]:
        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM claims")
        rows = [_claim_row(claim) for claim in claims]
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO claims (
                claim_id, domain, source, target, normalized_source, normalized_target,
                source_idx, target_idx, claim_type, terminal_form, verification_status,
                trust_level, provenance_type, metadata_json
            ) VALUES (
                :claim_id, :domain, :source, :target, :normalized_source, :normalized_target,
                :source_idx, :target_idx, :claim_type, :terminal_form, :verification_status,
                :trust_level, :provenance_type, :metadata_json
            )
            """,
            rows,
        )
        self.conn.commit()
        return {"imported": len(rows), "table": "claims"}

    def import_certificates(self, certificates: list[Any], replace: bool = False) -> dict[str, Any]:
        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM certificates")
        rows = [_certificate_row(cert) for cert in certificates]
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO certificates (
                certificate_id, claim_id, source_idx, target_idx, terminal_form,
                verification_status, trust_level, provenance_type, derivation_rule,
                route, payload_json, evidence_json
            ) VALUES (
                :certificate_id, :claim_id, :source_idx, :target_idx, :terminal_form,
                :verification_status, :trust_level, :provenance_type, :derivation_rule,
                :route, :payload_json, :evidence_json
            )
            """,
            rows,
        )
        self.conn.commit()
        return {"imported": len(rows), "table": "certificates"}

    def import_refutations(self, refutations: list[Any], replace: bool = False) -> dict[str, Any]:
        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM refutations")
        rows = [_refutation_row(row) for row in refutations]
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO refutations (
                refutation_id, claim_id, source, target, source_idx, target_idx,
                terminal_form, verification_status, trust_level, provenance_type,
                table_hash, table_name, table_json, witness_json, derivation_rule,
                elevation_method, payload_json
            ) VALUES (
                :refutation_id, :claim_id, :source, :target, :source_idx, :target_idx,
                :terminal_form, :verification_status, :trust_level, :provenance_type,
                :table_hash, :table_name, :table_json, :witness_json, :derivation_rule,
                :elevation_method, :payload_json
            )
            """,
            rows,
        )
        self.conn.commit()
        return {"imported": len(rows), "table": "refutations"}

    def import_roots(self, roots: list[Any], replace: bool = False) -> dict[str, Any]:
        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM roots")
        rows = [_root_store_row(root) for root in roots]
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO roots (
                root_node_id, canonical_name, root_type, root_key, table_motif,
                algebra_shape, source_target_basin, forced_transition, support_count,
                rows, unique_pairs, unique_sources, unique_targets, unique_tables,
                unique_motifs, load_bearing_score, status, payload_json
            ) VALUES (
                :root_node_id, :canonical_name, :root_type, :root_key, :table_motif,
                :algebra_shape, :source_target_basin, :forced_transition, :support_count,
                :rows, :unique_pairs, :unique_sources, :unique_targets, :unique_tables,
                :unique_motifs, :load_bearing_score, :status, :payload_json
            )
            """,
            rows,
        )
        self.conn.commit()
        return {"imported": len(rows), "table": "roots"}

    def import_reasons(self, reasons: list[Any], replace: bool = False) -> dict[str, Any]:
        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM reasons")
        rows = [_reason_store_row(reason) for reason in reasons]
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO reasons (
                reason_node_id, reason_type, reason_key, table_motif, algebra_shape,
                forced_transition, derivation_rule, support_count, rows, reason_score,
                status, payload_json
            ) VALUES (
                :reason_node_id, :reason_type, :reason_key, :table_motif, :algebra_shape,
                :forced_transition, :derivation_rule, :support_count, :rows, :reason_score,
                :status, :payload_json
            )
            """,
            rows,
        )
        self.conn.commit()
        return {"imported": len(rows), "table": "reasons"}

    def import_obstructions(self, obstructions: list[Any], replace: bool = False) -> dict[str, Any]:
        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM obstructions")
        rows = [_obstruction_store_row(obstruction) for obstruction in obstructions]
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO obstructions (
                obstruction_id, obstruction_signature, failure_reason, derivation_rule,
                source_target_basin, forced_transition, table_motif, rows,
                obstruction_pressure_score, payload_json
            ) VALUES (
                :obstruction_id, :obstruction_signature, :failure_reason, :derivation_rule,
                :source_target_basin, :forced_transition, :table_motif, :rows,
                :obstruction_pressure_score, :payload_json
            )
            """,
            rows,
        )
        self.conn.commit()
        return {"imported": len(rows), "table": "obstructions"}

    def import_root_aliases(self, aliases: list[Any], replace: bool = False) -> dict[str, Any]:
        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM root_aliases")
        rows = [_root_alias_store_row(alias) for alias in aliases]
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO root_aliases (
                alias, root_node_id, canonical_name, evidence_json
            ) VALUES (:alias, :root_node_id, :canonical_name, :evidence_json)
            """,
            rows,
        )
        self.conn.commit()
        return {"imported": len(rows), "table": "root_aliases"}

    def import_tables(self, tables: list[dict[str, Any]], replace: bool = False) -> dict[str, Any]:
        self.init_schema()
        if replace:
            self.conn.execute("DELETE FROM tables")
        rows = [_table_store_row(row) for row in tables]
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO tables (
                table_hash, table_name, table_json, motif, algebra_shape, payload_json
            ) VALUES (
                :table_hash, :table_name, :table_json, :motif, :algebra_shape, :payload_json
            )
            """,
            rows,
        )
        self.conn.commit()
        return {"imported": len(rows), "table": "tables"}

    def record_artifact_import(
        self,
        artifact_path: str | Path,
        artifact_kind: str,
        row_count: int,
        status: str = "imported",
        warnings: list[str] | None = None,
    ) -> None:
        from mathgraph.hashing import content_id

        self.init_schema()
        payload = {
            "artifact_path": str(artifact_path),
            "artifact_kind": artifact_kind,
            "row_count": row_count,
            "status": status,
        }
        self.conn.execute(
            """
            INSERT OR REPLACE INTO artifact_imports (
                import_id, artifact_path, artifact_kind, row_count, status,
                warnings_json, created_ts
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                content_id("artifact_import", payload),
                str(artifact_path),
                artifact_kind,
                int(row_count),
                status,
                json.dumps(warnings or [], sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def upsert_domain_kernel(self, kernel: Any) -> None:
        from mathgraph.domain_kernels import DomainKernel

        self.init_schema()
        data = kernel.to_dict() if hasattr(kernel, "to_dict") else DomainKernel.from_dict(dict(kernel)).to_dict()
        self.conn.execute(
            """
            INSERT OR REPLACE INTO domain_kernels (
                kernel_id, name, description, native_language, host_verifier,
                embedding_kind, source_uri, source_commit, trust_policy,
                ontology_summary_json, metadata_json, created_at, host_logic,
                object_logic, object_theory, artifact_risk, proof_transport_status,
                default_denotation_policy, default_type_system, default_identity_policy,
                default_hyperintensional_identity_policy, extensional_collapse_policy,
                workbench_id, workbench_layer, lifecycle_status, embedding_strategy,
                faithfulness_status, benchmark_status, default_formal_world_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["kernel_id"],
                data["name"],
                data.get("description", ""),
                data.get("native_language", ""),
                data["host_verifier"],
                data["embedding_kind"],
                data.get("source_uri", ""),
                data.get("source_commit", ""),
                data.get("trust_policy", ""),
                json.dumps(data.get("ontology_summary", []), sort_keys=True),
                json.dumps(data.get("metadata", {}), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
                data.get("host_logic", ""),
                data.get("object_logic", ""),
                data.get("object_theory", ""),
                data.get("artifact_risk", "UNKNOWN"),
                data.get("proof_transport_status", "NOT_ATTEMPTED"),
                data.get("default_denotation_policy", ""),
                data.get("default_type_system", ""),
                data.get("default_identity_policy", ""),
                data.get("default_hyperintensional_identity_policy", ""),
                data.get("extensional_collapse_policy", "NEVER_BY_DEFAULT"),
                data.get("workbench_id", ""),
                data.get("workbench_layer", ""),
                data.get("lifecycle_status", ""),
                data.get("embedding_strategy", ""),
                data.get("faithfulness_status", ""),
                data.get("benchmark_status", ""),
                data.get("default_formal_world_id", ""),
                data.get("notes", ""),
            ),
        )
        self.conn.commit()

    def get_domain_kernel(self, kernel_id_or_name: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute(
            """
            SELECT * FROM domain_kernels
            WHERE kernel_id = ? OR name = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (kernel_id_or_name, kernel_id_or_name),
        ).fetchone()
        return _domain_kernel_record(row) if row else None

    def list_domain_kernels(self, limit: int = 100) -> list[dict[str, Any]]:
        self.init_schema()
        rows = self.conn.execute(
            "SELECT * FROM domain_kernels ORDER BY name LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [_domain_kernel_record(row) for row in rows]

    def upsert_semantic_embedding(self, embedding: Any) -> None:
        from mathgraph.domain_kernels import SemanticEmbedding

        self.init_schema()
        data = (
            embedding.to_dict()
            if hasattr(embedding, "to_dict")
            else SemanticEmbedding.from_dict(dict(embedding)).to_dict()
        )
        self.conn.execute(
            """
            INSERT OR REPLACE INTO semantic_embeddings (
                embedding_id, domain_kernel_id, source_logic, target_logic,
                host_verifier, embedding_kind, description, soundness_status,
                artifact_uri, metadata_json, created_at, formal_world_id,
                host_logic, object_logic, object_theory, artifact_risk,
                object_theory_verified, host_embedding_verified,
                proof_transport_status, embedding_strategy_profile_id,
                faithfulness_assessment_id, syntax_representation,
                semantics_representation, automation_bias, notes, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["embedding_id"],
                data["domain_kernel_id"],
                data.get("source_logic", data.get("object_logic", "")),
                data.get("target_logic", data.get("host_logic", "")),
                data.get("host_verifier", ""),
                data.get("embedding_kind", ""),
                data.get("description", ""),
                data.get("soundness_status", data.get("proof_transport_status", "")),
                data.get("artifact_uri", ""),
                json.dumps(data.get("metadata", {}), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
                data.get("formal_world_id", ""),
                data.get("host_logic", data.get("target_logic", "")),
                data.get("object_logic", data.get("source_logic", "")),
                data.get("object_theory", ""),
                data.get("artifact_risk", "UNKNOWN"),
                int(bool(data.get("object_theory_verified", False))),
                int(bool(data.get("host_embedding_verified", False))),
                data.get("proof_transport_status", data.get("soundness_status", "")),
                data.get("embedding_strategy_profile_id"),
                data.get("faithfulness_assessment_id"),
                data.get("syntax_representation"),
                data.get("semantics_representation"),
                data.get("automation_bias"),
                data.get("notes", data.get("description", "")),
                json.dumps(data.get("payload", data), sort_keys=True),
            ),
        )
        self.conn.commit()

    def upsert_imported_theory_object(self, obj: Any) -> None:
        from mathgraph.domain_kernels import ImportedTheoryObject

        self.init_schema()
        data = obj.to_dict() if hasattr(obj, "to_dict") else ImportedTheoryObject.from_dict(dict(obj)).to_dict()
        self.conn.execute(
            """
            INSERT OR REPLACE INTO imported_theory_objects (
                object_id, domain_kernel_id, kind, name, statement, source_file,
                source_line, trust_level, provenance_type, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["object_id"],
                data["domain_kernel_id"],
                data["kind"],
                data.get("name", ""),
                data.get("statement", ""),
                data.get("source_file", ""),
                data.get("source_line"),
                data.get("trust_level", ""),
                data.get("provenance_type", ""),
                json.dumps(data.get("metadata", {}), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def upsert_imported_theory_relation(self, rel: Any) -> None:
        from mathgraph.domain_kernels import ImportedTheoryRelation

        self.init_schema()
        data = (
            rel.to_dict()
            if hasattr(rel, "to_dict")
            else ImportedTheoryRelation.from_dict(dict(rel)).to_dict()
        )
        self.conn.execute(
            """
            INSERT OR REPLACE INTO imported_theory_relations (
                relation_id, domain_kernel_id, source_object_id, target_object_id,
                relation_kind, trust_level, provenance_type, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["relation_id"],
                data["domain_kernel_id"],
                data.get("source_object_id", ""),
                data.get("target_object_id", ""),
                data["relation_kind"],
                data.get("trust_level", ""),
                data.get("provenance_type", ""),
                json.dumps(data.get("metadata", {}), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def domain_kernel_summary(self) -> dict[str, Any]:
        self.init_schema()
        counts = {
            name: self.conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            for name in (
                "domain_kernels",
                "semantic_embeddings",
                "imported_theory_objects",
                "imported_theory_relations",
                "typed_objects",
                "predication_facts",
                "denotation_records",
                "language_fragments",
                "theory_objectification_maps",
                "theory_denotations",
                "theory_readings",
                "analytic_truths",
                "formal_worlds",
                "paradox_guards",
                "reason_containment_records",
                "object_language_terms",
                "object_language_formulas",
                "theory_declarations",
                "proof_methods",
                "inference_rules",
                "isabelle_export_records",
                "host_object_theorem_links",
                "logical_workbenches",
                "embedding_strategy_profiles",
                "faithfulness_assessments",
                "logic_combinations",
                "verifier_backend_profiles",
                "proof_finder_results",
                "model_finder_results",
                "benchmark_suites",
                "benchmark_cases",
                "benchmark_runs",
                "benchmark_results",
                "correspondence_claims",
                "interpretation_choice_points",
                "proof_motifs",
                "lemma_candidates",
                "lean_artifacts",
                "proof_atlases",
            )
        }
        by_host = Counter(
            row["host_verifier"] for row in self.conn.execute("SELECT host_verifier FROM domain_kernels")
        )
        by_embedding = Counter(
            row["embedding_kind"] for row in self.conn.execute("SELECT embedding_kind FROM domain_kernels")
        )
        return {
            **counts,
            "by_host_verifier": dict(by_host),
            "by_embedding_kind": dict(by_embedding),
            "truth_boundary": "DomainKernel registration is metadata, not verification.",
        }

    def add_typed_object(self, obj: Any) -> None:
        self.init_schema()
        data = _as_dict(obj)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO typed_objects (
                object_id, type_expr, object_kind, domain_kernel_id, formal_world_id,
                ordinary_or_abstract, identity_mode, uniqueness_status,
                hyperintensional_identity_mode, label, encoded_properties_json,
                exemplified_properties_json, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["object_id"],
                data.get("type_expr", ""),
                data.get("object_kind", ""),
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                data.get("ordinary_or_abstract", "UNKNOWN"),
                data.get("identity_mode", "UNKNOWN"),
                data.get("uniqueness_status", "UNKNOWN"),
                data.get("hyperintensional_identity_mode", "UNKNOWN"),
                data.get("label"),
                json.dumps(data.get("encoded_properties", {}), sort_keys=True),
                json.dumps(data.get("exemplified_properties", {}), sort_keys=True),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_typed_objects(
        self,
        domain_kernel_id: str | None = None,
        formal_world_id: str | None = None,
        object_kind: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses, params = _filters(
            {
                "domain_kernel_id": domain_kernel_id,
                "formal_world_id": formal_world_id,
                "object_kind": object_kind,
            }
        )
        return [_typed_object_record(row) for row in self._select("typed_objects", clauses, params)]

    def get_typed_object(self, object_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute("SELECT * FROM typed_objects WHERE object_id = ?", (object_id,)).fetchone()
        return _typed_object_record(row) if row else None

    def add_predication_fact(self, fact: Any) -> None:
        self.init_schema()
        data = _as_dict(fact)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO predication_facts (
                predication_id, subject_id, predicate_id, mode, predicate_kind,
                domain_kernel_id, formal_world_id, trust_level, provenance_type,
                denotation_status, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["predication_id"],
                data.get("subject_id", ""),
                data.get("predicate_id", ""),
                data.get("mode", ""),
                data.get("predicate_kind", ""),
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                data.get("trust_level"),
                data.get("provenance_type"),
                data.get("denotation_status"),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_predication_facts(
        self,
        subject_id: str | None = None,
        mode: str | None = None,
        domain_kernel_id: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses, params = _filters(
            {"subject_id": subject_id, "mode": mode, "domain_kernel_id": domain_kernel_id}
        )
        return [_payload_record(row) for row in self._select("predication_facts", clauses, params)]

    def add_denotation_record(self, record: Any) -> None:
        self.init_schema()
        data = _as_dict(record)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO denotation_records (
                denotation_id, object_id, domain_kernel_id, formal_world_id,
                denotation_status, reason, checked_by, trust_level, provenance_type,
                payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["denotation_id"],
                data.get("object_id", ""),
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                data.get("denotation_status", ""),
                data.get("reason", ""),
                data.get("checked_by", ""),
                data.get("trust_level"),
                data.get("provenance_type"),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_denotation_records(
        self, object_id: str | None = None, domain_kernel_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"object_id": object_id, "domain_kernel_id": domain_kernel_id})
        return [_payload_record(row) for row in self._select("denotation_records", clauses, params)]

    def add_semantic_embedding(self, embedding: Any) -> None:
        self.upsert_semantic_embedding(embedding)

    def list_semantic_embeddings(self, domain_kernel_id: str | None = None) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id})
        return [_semantic_embedding_record(row) for row in self._select("semantic_embeddings", clauses, params)]

    def add_language_fragment(self, fragment: Any) -> None:
        self.init_schema()
        data = _as_dict(fragment)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO language_fragments (
                fragment_id, domain_kernel_id, formal_world_id, language_name,
                width_bound, height_bound, supported_type_exprs_json,
                supported_term_constructors_json, supported_claim_types_json,
                supported_verifiers_json, blocked_term_patterns_json,
                paradox_guard_policy, notes, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["fragment_id"],
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                data.get("language_name", ""),
                data.get("width_bound"),
                data.get("height_bound"),
                json.dumps(data.get("supported_type_exprs", []), sort_keys=True),
                json.dumps(data.get("supported_term_constructors", []), sort_keys=True),
                json.dumps(data.get("supported_claim_types", []), sort_keys=True),
                json.dumps(data.get("supported_verifiers", []), sort_keys=True),
                json.dumps(data.get("blocked_term_patterns", []), sort_keys=True),
                data.get("paradox_guard_policy"),
                data.get("notes", ""),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_language_fragments(self, domain_kernel_id: str | None = None) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id})
        return [_json_columns_record(row) for row in self._select("language_fragments", clauses, params)]

    def add_theory_objectification_map(self, map_obj: Any) -> None:
        self._insert_payload_table(
            "theory_objectification_maps",
            _as_dict(map_obj),
            "map_id",
            ("domain_kernel_id", "formal_world_id", "theory_id", "description", "trust_level", "provenance_type"),
        )

    def list_theory_objectification_maps(
        self, domain_kernel_id: str | None = None, theory_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "theory_id": theory_id})
        return [_payload_record(row) for row in self._select("theory_objectification_maps", clauses, params)]

    def add_theory_denotation(self, denotation: Any) -> None:
        self._insert_payload_table(
            "theory_denotations",
            _as_dict(denotation),
            "denotation_id",
            (
                "domain_kernel_id", "formal_world_id", "theory_id", "source_symbol",
                "source_kind", "target_object_id", "target_type_expr", "denotation_status",
                "trust_level", "provenance_type",
            ),
        )

    def list_theory_denotations(
        self, domain_kernel_id: str | None = None, theory_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "theory_id": theory_id})
        return [_payload_record(row) for row in self._select("theory_denotations", clauses, params)]

    def add_theory_reading(self, reading: Any) -> None:
        self._insert_payload_table(
            "theory_readings",
            _as_dict(reading),
            "reading_id",
            (
                "domain_kernel_id", "formal_world_id", "theory_id", "source_statement",
                "reading_statement", "reading_type_expr", "denotation_status",
                "trust_level", "provenance_type",
            ),
        )

    def list_theory_readings(
        self, domain_kernel_id: str | None = None, theory_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "theory_id": theory_id})
        return [_payload_record(row) for row in self._select("theory_readings", clauses, params)]

    def add_analytic_truth(self, truth: Any) -> None:
        self._insert_payload_table(
            "analytic_truths",
            _as_dict(truth),
            "analytic_truth_id",
            (
                "domain_kernel_id", "formal_world_id", "theory_id", "statement",
                "reading_id", "trust_level", "provenance_type", "verifier_id",
                "denotation_status",
            ),
        )

    def list_analytic_truths(
        self, domain_kernel_id: str | None = None, theory_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "theory_id": theory_id})
        return [_payload_record(row) for row in self._select("analytic_truths", clauses, params)]

    def add_formal_world(self, world: Any) -> None:
        self.init_schema()
        data = _as_dict(world)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO formal_worlds (
                formal_world_id, domain_kernel_id, name, world_kind, object_logic,
                identity_policy, denotation_policy, verifier_policy,
                language_fragment_ids_json, semantic_embedding_ids_json, notes,
                workbench_id, lifecycle_status, embedding_strategy_profile_ids_json,
                faithfulness_assessment_ids_json, benchmark_suite_ids_json,
                verifier_backend_ids_json, logic_combination_ids_json,
                interpretation_choice_ids_json, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["formal_world_id"],
                data.get("domain_kernel_id"),
                data.get("name", ""),
                data.get("world_kind", ""),
                data.get("object_logic", ""),
                data.get("identity_policy", ""),
                data.get("denotation_policy", ""),
                data.get("verifier_policy", ""),
                json.dumps(data.get("language_fragment_ids", []), sort_keys=True),
                json.dumps(data.get("semantic_embedding_ids", []), sort_keys=True),
                data.get("notes", ""),
                data.get("workbench_id"),
                data.get("lifecycle_status", "DECLARED"),
                json.dumps(data.get("embedding_strategy_profile_ids", []), sort_keys=True),
                json.dumps(data.get("faithfulness_assessment_ids", []), sort_keys=True),
                json.dumps(data.get("benchmark_suite_ids", []), sort_keys=True),
                json.dumps(data.get("verifier_backend_ids", []), sort_keys=True),
                json.dumps(data.get("logic_combination_ids", []), sort_keys=True),
                json.dumps(data.get("interpretation_choice_ids", []), sort_keys=True),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_formal_worlds(self, domain_kernel_id: str | None = None) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id})
        return [_json_columns_record(row) for row in self._select("formal_worlds", clauses, params)]

    def get_formal_world(self, formal_world_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute("SELECT * FROM formal_worlds WHERE formal_world_id = ?", (formal_world_id,)).fetchone()
        return _json_columns_record(row) if row else None

    def add_paradox_guard(self, guard: Any) -> None:
        self.init_schema()
        data = _as_dict(guard)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO paradox_guards (
                guard_id, domain_kernel_id, formal_world_id, guard_kind, name,
                description, severity, blocked_patterns_json, notes, payload_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["guard_id"],
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                data.get("guard_kind", ""),
                data.get("name", ""),
                data.get("description", ""),
                data.get("severity", ""),
                json.dumps(data.get("blocked_patterns", []), sort_keys=True),
                data.get("notes", ""),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_paradox_guards(
        self, domain_kernel_id: str | None = None, formal_world_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "formal_world_id": formal_world_id})
        return [_json_columns_record(row) for row in self._select("paradox_guards", clauses, params)]

    def add_reason_containment_record(self, record: Any) -> None:
        self._insert_payload_table(
            "reason_containment_records",
            _as_dict(record),
            "containment_id",
            (
                "reason_node_id", "domain_kernel_id", "formal_world_id", "source_id",
                "target_id", "containment_mode", "source_constraints", "target_demand",
                "separator_certificate_id", "trust_level", "provenance_type",
                "denotation_status",
            ),
        )

    def list_reason_containment_records(
        self, reason_node_id: str | None = None, domain_kernel_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"reason_node_id": reason_node_id, "domain_kernel_id": domain_kernel_id})
        return [_payload_record(row) for row in self._select("reason_containment_records", clauses, params)]

    def add_object_language_term(self, term: Any) -> None:
        self._insert_payload_table(
            "object_language_terms",
            _as_dict(term),
            "term_id",
            (
                "domain_kernel_id", "formal_world_id", "raw_text", "normalized_text",
                "type_expr", "denotation_status", "role",
            ),
        )

    def list_object_language_terms(
        self, domain_kernel_id: str | None = None, formal_world_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "formal_world_id": formal_world_id})
        return [_payload_record(row) for row in self._select("object_language_terms", clauses, params)]

    def add_object_language_formula(self, formula: Any) -> None:
        self._insert_payload_table(
            "object_language_formulas",
            _as_dict(formula),
            "formula_id",
            (
                "domain_kernel_id", "formal_world_id", "raw_text", "normalized_text",
                "type_expr", "formula_role", "denotation_status",
            ),
        )

    def list_object_language_formulas(
        self, domain_kernel_id: str | None = None, formal_world_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "formal_world_id": formal_world_id})
        return [_payload_record(row) for row in self._select("object_language_formulas", clauses, params)]

    def add_theory_declaration(self, declaration: Any) -> None:
        self._insert_payload_table(
            "theory_declarations",
            _as_dict(declaration),
            "declaration_id",
            (
                "domain_kernel_id", "formal_world_id", "theory_id", "declaration_kind",
                "name", "statement", "source_file", "source_line", "trust_level",
                "provenance_type", "host_logic", "object_logic", "object_theory_verified",
                "host_embedding_verified", "artifact_risk",
            ),
        )

    def list_theory_declarations(
        self,
        domain_kernel_id: str | None = None,
        theory_id: str | None = None,
        declaration_kind: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses, params = _filters(
            {"domain_kernel_id": domain_kernel_id, "theory_id": theory_id, "declaration_kind": declaration_kind}
        )
        return [_payload_record(row) for row in self._select("theory_declarations", clauses, params)]

    def add_proof_method(self, method: Any) -> None:
        self._insert_payload_table(
            "proof_methods",
            _as_dict(method),
            "proof_method_id",
            (
                "domain_kernel_id", "formal_world_id", "theory_id", "name",
                "method_kind", "source_file", "source_line", "trust_level",
                "provenance_type",
            ),
        )

    def list_proof_methods(
        self, domain_kernel_id: str | None = None, theory_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "theory_id": theory_id})
        return [_payload_record(row) for row in self._select("proof_methods", clauses, params)]

    def add_inference_rule(self, rule: Any) -> None:
        self._insert_payload_table(
            "inference_rules",
            _as_dict(rule),
            "inference_rule_id",
            (
                "domain_kernel_id", "formal_world_id", "theory_id", "name",
                "rule_kind", "statement", "source_file", "source_line",
                "trust_level", "provenance_type",
            ),
        )

    def list_inference_rules(
        self, domain_kernel_id: str | None = None, theory_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "theory_id": theory_id})
        return [_payload_record(row) for row in self._select("inference_rules", clauses, params)]

    def add_isabelle_export_record(self, record: Any) -> None:
        self._insert_payload_table(
            "isabelle_export_records",
            _as_dict(record),
            "export_id",
            (
                "domain_kernel_id", "formal_world_id", "theory_id", "name",
                "source_file", "host_logic", "object_logic", "export_status",
            ),
        )

    def list_isabelle_export_records(
        self, domain_kernel_id: str | None = None, theory_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "theory_id": theory_id})
        return [_payload_record(row) for row in self._select("isabelle_export_records", clauses, params)]

    def add_host_object_theorem_link(self, link: Any) -> None:
        self._insert_payload_table(
            "host_object_theorem_links",
            _as_dict(link),
            "link_id",
            (
                "domain_kernel_id", "formal_world_id", "theory_id", "host_theorem_id",
                "object_theorem_id", "export_status", "proof_transport_status",
                "artifact_risk",
            ),
        )

    def list_host_object_theorem_links(
        self, domain_kernel_id: str | None = None, theory_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "theory_id": theory_id})
        return [_payload_record(row) for row in self._select("host_object_theorem_links", clauses, params)]

    def add_logical_workbench(self, workbench: Any) -> None:
        self.init_schema()
        data = _as_dict(workbench)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO logical_workbenches (
                workbench_id, name, description, layer, domain_kernel_ids_json,
                formal_world_ids_json, logic_combination_ids_json,
                benchmark_suite_ids_json, lifecycle_status, notes, payload_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["workbench_id"],
                data.get("name", ""),
                data.get("description", ""),
                data.get("layer", ""),
                json.dumps(data.get("domain_kernel_ids", []), sort_keys=True),
                json.dumps(data.get("formal_world_ids", []), sort_keys=True),
                json.dumps(data.get("logic_combination_ids", []), sort_keys=True),
                json.dumps(data.get("benchmark_suite_ids", []), sort_keys=True),
                data.get("lifecycle_status", ""),
                data.get("notes", ""),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_logical_workbenches(
        self, layer: str | None = None, lifecycle_status: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"layer": layer, "lifecycle_status": lifecycle_status})
        return [_json_columns_record(row) for row in self._select("logical_workbenches", clauses, params)]

    def get_logical_workbench(self, workbench_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute("SELECT * FROM logical_workbenches WHERE workbench_id = ?", (workbench_id,)).fetchone()
        return _json_columns_record(row) if row else None

    def add_embedding_strategy_profile(self, profile: Any) -> None:
        self.init_schema()
        data = _as_dict(profile)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO embedding_strategy_profiles (
                profile_id, embedding_id, domain_kernel_id, formal_world_id,
                strategy, syntax_representation, semantics_representation,
                automation_bias, expected_strengths_json, expected_risks_json,
                notes, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["profile_id"],
                data.get("embedding_id"),
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                data.get("strategy", ""),
                data.get("syntax_representation", ""),
                data.get("semantics_representation", ""),
                data.get("automation_bias", ""),
                json.dumps(data.get("expected_strengths", []), sort_keys=True),
                json.dumps(data.get("expected_risks", []), sort_keys=True),
                data.get("notes", ""),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_embedding_strategy_profiles(
        self, domain_kernel_id: str | None = None, formal_world_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "formal_world_id": formal_world_id})
        return [_json_columns_record(row) for row in self._select("embedding_strategy_profiles", clauses, params)]

    def get_embedding_strategy_profile(self, profile_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute("SELECT * FROM embedding_strategy_profiles WHERE profile_id = ?", (profile_id,)).fetchone()
        return _json_columns_record(row) if row else None

    def add_faithfulness_assessment(self, assessment: Any) -> None:
        self._insert_payload_table(
            "faithfulness_assessments",
            _as_dict(assessment),
            "assessment_id",
            (
                "domain_kernel_id", "formal_world_id", "embedding_id", "object_logic",
                "host_logic", "status", "soundness_status", "completeness_status",
                "benchmark_suite_id", "proof_artifact_id", "counterexamples_found",
                "assessed_by", "notes",
            ),
        )

    def list_faithfulness_assessments(
        self, domain_kernel_id: str | None = None, embedding_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "embedding_id": embedding_id})
        return [_payload_record(row) for row in self._select("faithfulness_assessments", clauses, params)]

    def get_faithfulness_assessment(self, assessment_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute(
            "SELECT * FROM faithfulness_assessments WHERE assessment_id = ?", (assessment_id,)
        ).fetchone()
        return _payload_record(row) if row else None

    def add_logic_combination(self, combination: Any) -> None:
        self.init_schema()
        data = _as_dict(combination)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO logic_combinations (
                combination_id, name, component_kernel_ids_json,
                component_formal_world_ids_json, combination_method,
                shared_semantic_domains_json, interaction_axioms_json,
                conflict_policy, faithfulness_status, benchmark_status, notes,
                payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["combination_id"],
                data.get("name", ""),
                json.dumps(data.get("component_kernel_ids", []), sort_keys=True),
                json.dumps(data.get("component_formal_world_ids", []), sort_keys=True),
                data.get("combination_method", ""),
                json.dumps(data.get("shared_semantic_domains", []), sort_keys=True),
                json.dumps(data.get("interaction_axioms", []), sort_keys=True),
                data.get("conflict_policy", ""),
                data.get("faithfulness_status", "UNKNOWN"),
                data.get("benchmark_status", "UNKNOWN"),
                data.get("notes", ""),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_logic_combinations(self, domain_kernel_id: str | None = None) -> list[dict[str, Any]]:
        rows = self._select("logic_combinations", [], [])
        records = [_json_columns_record(row) for row in rows]
        if domain_kernel_id is not None:
            records = [row for row in records if domain_kernel_id in row.get("component_kernel_ids", [])]
        return records

    def get_logic_combination(self, combination_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute("SELECT * FROM logic_combinations WHERE combination_id = ?", (combination_id,)).fetchone()
        return _json_columns_record(row) if row else None

    def add_verifier_backend_profile(self, profile: Any) -> None:
        self.init_schema()
        data = _as_dict(profile)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO verifier_backend_profiles (
                backend_id, name, backend_kind, roles_json, host_logic,
                object_logic, supports_proofs, supports_models,
                produces_replayable_artifacts, native_to_domain_kernel,
                artifact_risk, notes, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["backend_id"],
                data.get("name", ""),
                data.get("backend_kind", ""),
                json.dumps(data.get("roles", []), sort_keys=True),
                data.get("host_logic"),
                data.get("object_logic"),
                int(bool(data.get("supports_proofs", False))),
                int(bool(data.get("supports_models", False))),
                int(bool(data.get("produces_replayable_artifacts", False))),
                int(bool(data.get("native_to_domain_kernel", False))),
                data.get("artifact_risk", "UNKNOWN"),
                data.get("notes", ""),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_verifier_backend_profiles(
        self, backend_kind: str | None = None, role: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"backend_kind": backend_kind})
        records = [_json_columns_record(row) for row in self._select("verifier_backend_profiles", clauses, params)]
        for record in records:
            record["supports_proofs"] = bool(record.get("supports_proofs"))
            record["supports_models"] = bool(record.get("supports_models"))
            record["produces_replayable_artifacts"] = bool(record.get("produces_replayable_artifacts"))
            record["native_to_domain_kernel"] = bool(record.get("native_to_domain_kernel"))
        if role is not None:
            records = [row for row in records if role in row.get("roles", [])]
        return records

    def get_verifier_backend_profile(self, backend_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute("SELECT * FROM verifier_backend_profiles WHERE backend_id = ?", (backend_id,)).fetchone()
        if not row:
            return None
        record = _json_columns_record(row)
        for key in ("supports_proofs", "supports_models", "produces_replayable_artifacts", "native_to_domain_kernel"):
            record[key] = bool(record.get(key))
        return record

    def add_proof_finder_result(self, result: Any) -> None:
        self._insert_payload_table(
            "proof_finder_results",
            _as_dict(result),
            "result_id",
            (
                "claim_id", "backend_id", "domain_kernel_id", "formal_world_id",
                "status", "proof_artifact_id", "proof_text", "runtime_sec",
                "trust_level", "provenance_type", "artifact_risk", "notes",
            ),
        )

    def list_proof_finder_results(
        self, claim_id: str | None = None, backend_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"claim_id": claim_id, "backend_id": backend_id})
        return [_payload_record(row) for row in self._select("proof_finder_results", clauses, params)]

    def add_model_finder_result(self, result: Any) -> None:
        data = _as_dict(result)
        data["model_payload_json"] = data.get("model_payload", {})
        data["scope_bounds_json"] = data.get("scope_bounds", {})
        self._insert_payload_table(
            "model_finder_results",
            data,
            "result_id",
            (
                "claim_id", "backend_id", "domain_kernel_id", "formal_world_id",
                "status", "model_artifact_id", "model_payload_json",
                "scope_bounds_json", "runtime_sec", "trust_level",
                "provenance_type", "artifact_risk", "notes",
            ),
        )

    def list_model_finder_results(
        self, claim_id: str | None = None, backend_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"claim_id": claim_id, "backend_id": backend_id})
        return [_json_columns_record(row) for row in self._select("model_finder_results", clauses, params)]

    def add_benchmark_suite(self, suite: Any) -> None:
        self._insert_payload_table(
            "benchmark_suites",
            _as_dict(suite),
            "suite_id",
            ("name", "domain_kernel_id", "formal_world_id", "description", "case_count", "source", "notes"),
        )

    def list_benchmark_suites(
        self, domain_kernel_id: str | None = None, formal_world_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "formal_world_id": formal_world_id})
        return [_payload_record(row) for row in self._select("benchmark_suites", clauses, params)]

    def get_benchmark_suite(self, suite_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute("SELECT * FROM benchmark_suites WHERE suite_id = ?", (suite_id,)).fetchone()
        return _payload_record(row) if row else None

    def add_benchmark_case(self, case: Any) -> None:
        self._insert_payload_table(
            "benchmark_cases",
            _as_dict(case),
            "case_id",
            (
                "suite_id", "claim_id", "source_statement", "target_statement",
                "expected_status", "expected_terminal_form", "notes",
            ),
        )

    def list_benchmark_cases(self, suite_id: str | None = None) -> list[dict[str, Any]]:
        clauses, params = _filters({"suite_id": suite_id})
        return [_payload_record(row) for row in self._select("benchmark_cases", clauses, params)]

    def add_benchmark_run(self, run: Any) -> None:
        self._insert_payload_table(
            "benchmark_runs",
            _as_dict(run),
            "run_id",
            (
                "suite_id", "backend_id", "domain_kernel_id", "formal_world_id",
                "started_at", "finished_at", "total_cases", "passed_cases",
                "failed_cases", "unknown_cases", "notes",
            ),
        )

    def list_benchmark_runs(self, suite_id: str | None = None) -> list[dict[str, Any]]:
        clauses, params = _filters({"suite_id": suite_id})
        return [_payload_record(row) for row in self._select("benchmark_runs", clauses, params)]

    def add_benchmark_result(self, result: Any) -> None:
        self._insert_payload_table(
            "benchmark_results",
            _as_dict(result),
            "result_id",
            (
                "run_id", "case_id", "observed_status", "expected_status",
                "verifier_backend_id", "runtime_sec", "proof_result_id",
                "model_result_id", "artifact_risk", "regression_status", "notes",
            ),
        )

    def list_benchmark_results(
        self, run_id: str | None = None, case_id: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"run_id": run_id, "case_id": case_id})
        return [_payload_record(row) for row in self._select("benchmark_results", clauses, params)]

    def add_correspondence_claim(self, claim: Any) -> None:
        self._insert_payload_table(
            "correspondence_claims",
            _as_dict(claim),
            "correspondence_id",
            (
                "domain_kernel_id", "formal_world_id", "semantic_condition_id",
                "syntactic_axiom_id", "source_object_id", "target_object_id",
                "direction", "status", "proof_artifact_id", "countermodel_artifact_id",
                "benchmark_suite_id", "trust_level", "provenance_type", "notes",
            ),
        )

    def list_correspondence_claims(
        self, domain_kernel_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "status": status})
        return [_payload_record(row) for row in self._select("correspondence_claims", clauses, params)]

    def get_correspondence_claim(self, correspondence_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute(
            "SELECT * FROM correspondence_claims WHERE correspondence_id = ?", (correspondence_id,)
        ).fetchone()
        return _payload_record(row) if row else None

    def add_interpretation_choice_point(self, choice: Any) -> None:
        self.init_schema()
        data = _as_dict(choice)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO interpretation_choice_points (
                choice_id, domain_kernel_id, formal_world_id, ambiguous_symbol,
                context, candidate_readings_json, selected_reading_id,
                rejected_reading_ids_json, downstream_effects_json, status,
                trust_level, provenance_type, notes, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["choice_id"],
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                data.get("ambiguous_symbol", ""),
                data.get("context", ""),
                json.dumps(data.get("candidate_readings", []), sort_keys=True),
                data.get("selected_reading_id"),
                json.dumps(data.get("rejected_reading_ids", []), sort_keys=True),
                json.dumps(data.get("downstream_effects", []), sort_keys=True),
                data.get("status", "OPEN"),
                data.get("trust_level", "ADVISORY_ROUTE"),
                data.get("provenance_type", "IMPORTED"),
                data.get("notes", ""),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_interpretation_choice_points(
        self, domain_kernel_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id, "status": status})
        return [_json_columns_record(row) for row in self._select("interpretation_choice_points", clauses, params)]

    def get_interpretation_choice_point(self, choice_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute(
            "SELECT * FROM interpretation_choice_points WHERE choice_id = ?", (choice_id,)
        ).fetchone()
        return _json_columns_record(row) if row else None

    def add_proof_motif(self, motif: Any) -> None:
        self.init_schema()
        data = _as_dict(motif)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO proof_motifs (
                proof_motif_id, motif_kind, domain_kernel_id, formal_world_id,
                source_basin, target_basin, source_shape, target_shape,
                route_signature, normalized_pattern, support_count, unique_sources,
                unique_targets, unique_claims, example_claim_ids_json,
                example_source_idxs_json, example_target_idxs_json, trust_level,
                provenance_type, verification_status, status, payload_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["proof_motif_id"],
                data.get("motif_kind", ""),
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                data.get("source_basin"),
                data.get("target_basin"),
                data.get("source_shape"),
                data.get("target_shape"),
                data.get("route_signature"),
                data.get("normalized_pattern"),
                data.get("support_count", 0),
                data.get("unique_sources", 0),
                data.get("unique_targets", 0),
                data.get("unique_claims", 0),
                json.dumps(data.get("example_claim_ids", []), sort_keys=True),
                json.dumps(data.get("example_source_idxs", []), sort_keys=True),
                json.dumps(data.get("example_target_idxs", []), sort_keys=True),
                data.get("trust_level", "ADVISORY_ROUTE"),
                data.get("provenance_type", "IMPORTED"),
                data.get("verification_status", "UNKNOWN"),
                data.get("status", "ADVISORY"),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_proof_motifs(
        self,
        domain_kernel_id: str | None = None,
        motif_kind: str | None = None,
        verification_status: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses, params = _filters(
            {"domain_kernel_id": domain_kernel_id, "motif_kind": motif_kind, "verification_status": verification_status}
        )
        records = [_json_columns_record(row) for row in self._select("proof_motifs", clauses, params)]
        records.sort(key=lambda row: (row.get("support_count") or 0, row.get("unique_claims") or 0), reverse=True)
        return records[:limit] if limit is not None else records

    def get_proof_motif(self, proof_motif_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute("SELECT * FROM proof_motifs WHERE proof_motif_id = ?", (proof_motif_id,)).fetchone()
        return _json_columns_record(row) if row else None

    def add_lemma_candidate(self, candidate: Any) -> None:
        self.init_schema()
        data = _as_dict(candidate)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO lemma_candidates (
                lemma_candidate_id, candidate_name, domain_kernel_id, formal_world_id,
                proof_motif_id, reason_node_id, root_node_id, cut_kind,
                statement_text, normalized_statement, lean_statement, lean_sketch,
                expected_covered_claims, example_claim_ids_json,
                example_source_idxs_json, example_target_idxs_json, status,
                trust_level, provenance_type, verification_status, verifier_id,
                proof_artifact_id, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["lemma_candidate_id"],
                data.get("candidate_name", ""),
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                data.get("proof_motif_id"),
                data.get("reason_node_id"),
                data.get("root_node_id"),
                data.get("cut_kind", ""),
                data.get("statement_text", ""),
                data.get("normalized_statement"),
                data.get("lean_statement"),
                data.get("lean_sketch"),
                data.get("expected_covered_claims", 0),
                json.dumps(data.get("example_claim_ids", []), sort_keys=True),
                json.dumps(data.get("example_source_idxs", []), sort_keys=True),
                json.dumps(data.get("example_target_idxs", []), sort_keys=True),
                data.get("status", "CANDIDATE"),
                data.get("trust_level", "ADVISORY_ROUTE"),
                data.get("provenance_type", "GENERATED"),
                data.get("verification_status", "UNKNOWN"),
                data.get("verifier_id"),
                data.get("proof_artifact_id"),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_lemma_candidates(
        self,
        domain_kernel_id: str | None = None,
        status: str | None = None,
        verification_status: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses, params = _filters(
            {"domain_kernel_id": domain_kernel_id, "status": status, "verification_status": verification_status}
        )
        records = [_json_columns_record(row) for row in self._select("lemma_candidates", clauses, params)]
        records.sort(key=lambda row: row.get("expected_covered_claims") or 0, reverse=True)
        return records[:limit] if limit is not None else records

    def get_lemma_candidate(self, lemma_candidate_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute(
            "SELECT * FROM lemma_candidates WHERE lemma_candidate_id = ?", (lemma_candidate_id,)
        ).fetchone()
        return _json_columns_record(row) if row else None

    def add_lean_artifact(self, artifact: Any) -> None:
        self.init_schema()
        data = _as_dict(artifact)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO lean_artifacts (
                lean_artifact_id, artifact_kind, name, domain_kernel_id,
                formal_world_id, theorem_name, statement, proof_text, imports_json,
                depends_on_json, verification_status, trust_level, provenance_type,
                source_file, line_start, line_end, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["lean_artifact_id"],
                data.get("artifact_kind", ""),
                data.get("name", ""),
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                data.get("theorem_name"),
                data.get("statement"),
                data.get("proof_text"),
                json.dumps(data.get("imports", []), sort_keys=True),
                json.dumps(data.get("depends_on", []), sort_keys=True),
                data.get("verification_status", "NOT_ATTEMPTED"),
                data.get("trust_level", "ADVISORY_ROUTE"),
                data.get("provenance_type", "GENERATED"),
                data.get("source_file"),
                data.get("line_start"),
                data.get("line_end"),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_lean_artifacts(
        self,
        domain_kernel_id: str | None = None,
        verification_status: str | None = None,
        artifact_kind: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses, params = _filters(
            {"domain_kernel_id": domain_kernel_id, "verification_status": verification_status, "artifact_kind": artifact_kind}
        )
        records = [_json_columns_record(row) for row in self._select("lean_artifacts", clauses, params)]
        return records[:limit] if limit is not None else records

    def get_lean_artifact(self, lean_artifact_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute("SELECT * FROM lean_artifacts WHERE lean_artifact_id = ?", (lean_artifact_id,)).fetchone()
        return _json_columns_record(row) if row else None

    def add_proof_atlas(self, atlas: Any) -> None:
        self.init_schema()
        data = _as_dict(atlas)
        motifs = data.get("proof_motifs", [])
        candidates = data.get("lemma_candidates", [])
        artifacts = data.get("lean_artifacts", [])
        self.conn.execute(
            """
            INSERT OR REPLACE INTO proof_atlases (
                atlas_id, domain_kernel_id, formal_world_id, proof_motif_ids_json,
                lemma_candidate_ids_json, lean_artifact_ids_json, payload_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["atlas_id"],
                data.get("domain_kernel_id"),
                data.get("formal_world_id"),
                json.dumps([_row_id(row, "proof_motif_id") for row in motifs], sort_keys=True),
                json.dumps([_row_id(row, "lemma_candidate_id") for row in candidates], sort_keys=True),
                json.dumps([_row_id(row, "lean_artifact_id") for row in artifacts], sort_keys=True),
                json.dumps(data.get("payload", data), sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def list_proof_atlases(
        self, domain_kernel_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        clauses, params = _filters({"domain_kernel_id": domain_kernel_id})
        records = [_json_columns_record(row) for row in self._select("proof_atlases", clauses, params)]
        return records[:limit] if limit is not None else records

    def get_proof_atlas(self, atlas_id: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute("SELECT * FROM proof_atlases WHERE atlas_id = ?", (atlas_id,)).fetchone()
        return _json_columns_record(row) if row else None

    def _select(self, table: str, clauses: list[str], params: list[Any]) -> list[sqlite3.Row]:
        self.init_schema()
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        return self.conn.execute(f"SELECT * FROM {table}{where} ORDER BY 1", tuple(params)).fetchall()

    def _insert_payload_table(
        self, table: str, data: dict[str, Any], id_key: str, columns: tuple[str, ...]
    ) -> None:
        self.init_schema()
        names = (id_key, *columns, "payload_json", "created_at")
        placeholders = ", ".join("?" for _ in names)
        values = [
            data[id_key],
            *(_sql_value(data.get(name)) for name in columns),
            json.dumps(data.get("payload", data), sort_keys=True),
            datetime.now(timezone.utc).isoformat(),
        ]
        self.conn.execute(
            f"INSERT OR REPLACE INTO {table} ({', '.join(names)}) VALUES ({placeholders})",
            values,
        )
        self.conn.commit()

    def stats(self) -> LawbookStoreStats:
        self.init_schema()
        rows = [dict(row) for row in self.conn.execute("SELECT * FROM traces")]
        return LawbookStoreStats(
            trace_count=len(rows),
            claim_count=len({row["claim"] for row in rows}),
            certificate_count=sum(1 for row in rows if row["certificate_json"]),
            pair_count=len({(row["source"], row["target"]) for row in rows}),
            source_count=len({row["source"] for row in rows if row["source"] is not None}),
            target_count=len({row["target"] for row in rows if row["target"] is not None}),
            route_counts=dict(Counter(row["compiled_route"] for row in rows if row["compiled_route"])),
            terminal_form_counts=dict(Counter(row["terminal_form"] for row in rows)),
            verification_status_counts=dict(Counter(row["verification_status"] for row in rows)),
        )

    def get_by_claim(self, claim: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM traces WHERE claim = ? OR claim_hash = ? ORDER BY id LIMIT 1",
            (claim, claim),
        ).fetchone()
        return _row_to_record(row) if row else None

    def get_by_pair(self, source: str, target: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT * FROM traces
            WHERE (source = ? AND target = ?) OR (source_idx = ? AND target_idx = ?)
            ORDER BY id LIMIT 1
            """,
            (str(source), str(target), str(source), str(target)),
        ).fetchone()
        return _row_to_record(row) if row else None

    def get_derived_by_pair(self, source: str, target: str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute(
            """
            SELECT * FROM derived_certificates
            WHERE source = ? AND target = ?
            ORDER BY id LIMIT 1
            """,
            (str(source), str(target)),
        ).fetchone()
        return _derived_row_to_record(row) if row else None

    def find_derived_by_rule(self, rule: str, limit: int = 50) -> list[dict[str, Any]]:
        self.init_schema()
        rows = self.conn.execute(
            """
            SELECT * FROM derived_certificates
            WHERE derivation_rule = ?
            ORDER BY id LIMIT ?
            """,
            (rule, int(limit)),
        ).fetchall()
        return [_derived_row_to_record(row) for row in rows]

    def derived_stats(self) -> dict[str, Any]:
        self.init_schema()
        rows = [dict(row) for row in self.conn.execute("SELECT * FROM derived_certificates")]
        return {
            "total": len(rows),
            "terminal_form_counts": dict(Counter(row["terminal_form"] for row in rows)),
            "verification_status_counts": dict(
                Counter(row["verification_status"] for row in rows)
            ),
            "rule_counts": dict(Counter(row["derivation_rule"] for row in rows)),
            "trust_level_counts": dict(Counter(row["trust_level"] for row in rows)),
        }

    def iter_primitive_traces(self, limit: int | None = None) -> Iterator[dict[str, Any]]:
        self.init_schema()
        query = "SELECT * FROM traces ORDER BY id"
        params: tuple[Any, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (int(limit),)
        for row in self.conn.execute(query, params):
            yield _row_to_record(row)

    def iter_derived_certificates(self, limit: int | None = None) -> Iterator[dict[str, Any]]:
        self.init_schema()
        query = "SELECT * FROM derived_certificates ORDER BY id"
        params: tuple[Any, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (int(limit),)
        for row in self.conn.execute(query, params):
            yield _derived_row_to_record(row)

    def primitive_stats(self) -> dict[str, Any]:
        return self.stats().to_dict()

    def full_certificate_stats(self) -> dict[str, Any]:
        primitive = self.stats().to_dict()
        derived = self.derived_stats()
        warehouse = self.warehouse_summary()
        terminal_counts = Counter(primitive["terminal_form_counts"])
        terminal_counts.update(derived["terminal_form_counts"])
        terminal_counts.update(warehouse.get("certificate_terminal_form_counts", {}))
        trust_counts = Counter({"primitive_trace": primitive["trace_count"]})
        trust_counts.update(derived.get("trust_level_counts", {}))
        return {
            "primitive": primitive,
            "derived": derived,
            "warehouse": warehouse,
            "total_certificate_count": primitive["trace_count"] + derived["total"],
            "by_terminal_form": dict(terminal_counts),
            "by_trust_level": dict(trust_counts),
        }

    def warehouse_summary(self) -> dict[str, Any]:
        self.init_schema()
        counts = {
            name: self.conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            for name in (
                "claims",
                "certificates",
                "refutations",
                "roots",
                "root_aliases",
                "reasons",
                "obstructions",
                "tables",
                "artifact_imports",
                "domain_kernels",
                "semantic_embeddings",
                "imported_theory_objects",
                "imported_theory_relations",
                "typed_objects",
                "predication_facts",
                "denotation_records",
                "language_fragments",
                "theory_objectification_maps",
                "theory_denotations",
                "theory_readings",
                "analytic_truths",
                "formal_worlds",
                "paradox_guards",
                "reason_containment_records",
                "object_language_terms",
                "object_language_formulas",
                "theory_declarations",
                "proof_methods",
                "inference_rules",
                "isabelle_export_records",
                "host_object_theorem_links",
                "logical_workbenches",
                "embedding_strategy_profiles",
                "faithfulness_assessments",
                "logic_combinations",
                "verifier_backend_profiles",
                "proof_finder_results",
                "model_finder_results",
                "benchmark_suites",
                "benchmark_cases",
                "benchmark_runs",
                "benchmark_results",
                "correspondence_claims",
                "interpretation_choice_points",
                "proof_motifs",
                "lemma_candidates",
                "lean_artifacts",
                "proof_atlases",
            )
        }
        cert_rows = [dict(row) for row in self.conn.execute("SELECT terminal_form FROM certificates")]
        verified_lean_count = self.conn.execute(
            "SELECT COUNT(*) FROM lean_artifacts WHERE verification_status IN ('LEAN_VERIFIED', 'IMPORTED_VERIFIED')"
        ).fetchone()[0]
        return {
            **counts,
            "certificate_terminal_form_counts": dict(Counter(row["terminal_form"] for row in cert_rows)),
            "verified_lean_artifacts": verified_lean_count,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "primitive": self.stats().to_dict(),
            "derived": self.derived_stats(),
            "warehouse": self.warehouse_summary(),
            "domain_kernels": self.domain_kernel_summary(),
            "truth_boundary": "Root/reason/obstruction rows are advisory unless backed by concrete certificate chains.",
        }

    def query_claim(self, source_idx: int | str, target_idx: int | str) -> dict[str, Any]:
        self.init_schema()
        row = self.conn.execute(
            """
            SELECT * FROM claims
            WHERE source_idx = ? AND target_idx = ?
            ORDER BY claim_id LIMIT 1
            """,
            (str(source_idx), str(target_idx)),
        ).fetchone()
        if row:
            return _claim_record(row)
        primitive = self.get_by_pair(str(source_idx), str(target_idx))
        if primitive is not None:
            return primitive
        return {
            "status": "missing",
            "source_idx": str(source_idx),
            "target_idx": str(target_idx),
            "terminal_form": "NAMED_OBSTRUCTION",
            "verification_status": "UNKNOWN",
            "advisory_only": True,
            "explanation": "No exact verified claim found.",
        }

    def query_refutation(self, source_idx: int | str, target_idx: int | str) -> dict[str, Any] | None:
        self.init_schema()
        row = self.conn.execute(
            """
            SELECT * FROM refutations
            WHERE (source_idx = ? AND target_idx = ?) OR (source = ? AND target = ?)
            ORDER BY refutation_id LIMIT 1
            """,
            (str(source_idx), str(target_idx), str(source_idx), str(target_idx)),
        ).fetchone()
        return _refutation_record(row) if row else None

    def top_roots(self, limit: int = 20) -> list[dict[str, Any]]:
        self.init_schema()
        rows = self.conn.execute(
            "SELECT * FROM roots ORDER BY load_bearing_score DESC, rows DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [_root_store_record(row) for row in rows]

    def top_reasons(self, limit: int = 20) -> list[dict[str, Any]]:
        self.init_schema()
        rows = self.conn.execute(
            "SELECT * FROM reasons ORDER BY reason_score DESC, rows DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [_reason_store_record(row) for row in rows]

    def top_obstructions(self, limit: int = 20) -> list[dict[str, Any]]:
        self.init_schema()
        rows = self.conn.execute(
            "SELECT * FROM obstructions ORDER BY obstruction_pressure_score DESC, rows DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [_obstruction_store_record(row) for row in rows]

    def explain_root(self, root_id: str) -> dict[str, Any]:
        self.init_schema()
        row = self.conn.execute(
            "SELECT * FROM roots WHERE root_node_id = ? OR canonical_name = ? LIMIT 1",
            (root_id, root_id),
        ).fetchone()
        if not row:
            return {"status": "missing", "root_id": root_id, "advisory_only": True}
        root = _root_store_record(row)
        return {
            "status": "hit",
            "root": root,
            "advisory_only": True,
            "explanation": f"{root['canonical_name']} compresses certificate motifs but is not itself verification.",
        }

    def explain_reason(self, reason_id: str) -> dict[str, Any]:
        self.init_schema()
        row = self.conn.execute(
            "SELECT * FROM reasons WHERE reason_node_id = ? OR reason_key = ? LIMIT 1",
            (reason_id, reason_id),
        ).fetchone()
        if not row:
            return {"status": "missing", "reason_id": reason_id, "advisory_only": True}
        reason = _reason_store_record(row)
        return {
            "status": "hit",
            "reason": reason,
            "advisory_only": True,
            "explanation": "Reason nodes compress explanation patterns; they do not promote claims.",
        }

    def explain_obstruction(self, obstruction_id: str) -> dict[str, Any]:
        self.init_schema()
        row = self.conn.execute(
            "SELECT * FROM obstructions WHERE obstruction_id = ? OR obstruction_signature = ? LIMIT 1",
            (obstruction_id, obstruction_id),
        ).fetchone()
        if not row:
            return {"status": "missing", "obstruction_id": obstruction_id, "advisory_only": True}
        obstruction = _obstruction_store_record(row)
        return {
            "status": "hit",
            "obstruction": obstruction,
            "advisory_only": True,
            "explanation": "Obstruction nodes name residual pressure; they are not proof or refutation.",
        }

    def find_by_source(self, source: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._find("source = ? OR source_idx = ?", (str(source), str(source)), limit)

    def find_by_target(self, target: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._find("target = ? OR target_idx = ?", (str(target), str(target)), limit)

    def find_by_route(self, route: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._find("compiled_route = ?", (route,), limit)

    def find_by_terminal_form(self, terminal_form: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._find("terminal_form = ?", (terminal_form,), limit)

    def explain_claim(self, claim: str) -> dict[str, Any]:
        return self.get_by_claim(claim) or _missing_record(claim=claim)

    def explain_pair(self, source: str, target: str) -> dict[str, Any]:
        return self.get_by_pair(source, target) or _missing_record(source=source, target=target)

    def _find(self, where: str, params: tuple[Any, ...], limit: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            f"SELECT * FROM traces WHERE {where} ORDER BY id LIMIT ?",
            (*params, int(limit)),
        ).fetchall()
        return [_row_to_record(row) for row in rows]


def _trace_row(trace: Trace) -> dict[str, Any]:
    metadata = dict(trace.metadata or {})
    cert = trace.certificate.to_dict() if trace.certificate else None
    payload = trace.certificate.payload if trace.certificate else {}
    return {
        "claim": trace.claim,
        "claim_hash": _trace_value(trace, "claim_hash"),
        "source": trace.source or _trace_value(trace, "source_equation"),
        "target": trace.target or _trace_value(trace, "target_equation"),
        "source_idx": _trace_value(trace, "source_idx"),
        "target_idx": _trace_value(trace, "target_idx"),
        "compiled_route": _trace_value(trace, "compiled_route") or (trace.routes_tried[0] if trace.routes_tried else None),
        "terminal_form": trace.terminal_form.value,
        "verification_status": trace.verification_status.value,
        "promotion_status": _trace_value(trace, "promotion_status"),
        "lean_status": _trace_value(trace, "lean_status"),
        "certificate_id": str(payload.get("proof_id") or payload.get("certificate_id") or "") or None,
        "certificate_payload_keys_json": json.dumps(sorted(payload.keys()), sort_keys=True),
        "metadata_keys_json": json.dumps(sorted(metadata.keys()), sort_keys=True),
        "trace_json": json.dumps(trace.to_dict(), sort_keys=True),
        "certificate_json": json.dumps(cert, sort_keys=True) if cert else None,
        "metadata_json": json.dumps(metadata, sort_keys=True),
        "created": trace.created,
    }


def _derived_row(cert: "DerivedCertificate") -> dict[str, Any]:
    return {
        "derived_claim": cert.derived_claim,
        "source": cert.source,
        "target": cert.target,
        "source_idx": str(cert.source_idx) if cert.source_idx is not None else None,
        "target_idx": str(cert.target_idx) if cert.target_idx is not None else None,
        "terminal_form": cert.terminal_form,
        "verification_status": cert.verification_status,
        "derivation_rule": cert.derivation_rule,
        "trust_level": cert.trust_level,
        "parent_claims_json": json.dumps(cert.parent_claims, sort_keys=True),
        "parent_pairs_json": json.dumps(cert.parent_pairs, sort_keys=True),
        "route": cert.route,
        "explanation": cert.explanation,
        "evidence_json": json.dumps(cert.evidence, sort_keys=True),
        "warnings_json": json.dumps(cert.warnings, sort_keys=True),
        "created_ts": datetime.now(timezone.utc).isoformat(),
    }


def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    return {
        "status": "hit",
        "claim": data["claim"],
        "claim_hash": data["claim_hash"],
        "source": data["source"],
        "target": data["target"],
        "source_idx": data["source_idx"],
        "target_idx": data["target_idx"],
        "route": data["compiled_route"],
        "compiled_route": data["compiled_route"],
        "terminal_form": data["terminal_form"],
        "verification_status": data["verification_status"],
        "promotion_status": data["promotion_status"],
        "lean_status": data["lean_status"],
        "certificate_id": data["certificate_id"],
        "certificate_payload_keys": json.loads(data["certificate_payload_keys_json"]),
        "metadata_keys": json.loads(data["metadata_keys_json"]),
        "created": data["created"],
        "trace": json.loads(data["trace_json"]),
        "certificate": json.loads(data["certificate_json"]) if data["certificate_json"] else None,
        "metadata": json.loads(data["metadata_json"]),
        "explanation": "Exact verified lawbook trace found.",
    }


def _derived_row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    return {
        "status": "derived_hit",
        "claim": data["derived_claim"],
        "derived_claim": data["derived_claim"],
        "source": data["source"],
        "target": data["target"],
        "source_idx": data["source_idx"],
        "target_idx": data["target_idx"],
        "route": data["route"],
        "terminal_form": data["terminal_form"],
        "verification_status": data["verification_status"],
        "derivation_rule": data["derivation_rule"],
        "trust_level": data["trust_level"],
        "parent_claims": json.loads(data["parent_claims_json"]),
        "parent_pairs": json.loads(data["parent_pairs_json"]),
        "evidence": json.loads(data["evidence_json"]),
        "warnings": json.loads(data["warnings_json"]),
        "explanation": data["explanation"],
        "created": data["created_ts"],
        "certificate_id": data["derived_claim"],
    }


def _missing_record(
    claim: str | None = None,
    source: str | None = None,
    target: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "missing",
        "claim": claim,
        "source": source,
        "target": target,
        "route": None,
        "terminal_form": "NAMED_OBSTRUCTION",
        "verification_status": "UNKNOWN",
        "explanation": "No exact verified lawbook trace found.",
    }


def _claim_row(claim: Any) -> dict[str, Any]:
    data = _as_dict(claim)
    source = _pick(data, "source", "source_equation")
    target = _pick(data, "target", "target_equation")
    source_idx = _pick(data, "source_idx", "source_id")
    target_idx = _pick(data, "target_idx", "target_id")
    claim_id = str(_pick(data, "claim_id", "claim", "claim_hash") or _warehouse_id("claim", data))
    return {
        "claim_id": claim_id,
        "domain": str(data.get("domain", "magma_equation")),
        "source": source,
        "target": target,
        "normalized_source": _normalize_text(_pick(data, "normalized_source") or source),
        "normalized_target": _normalize_text(_pick(data, "normalized_target") or target),
        "source_idx": _str_or_none(source_idx),
        "target_idx": _str_or_none(target_idx),
        "claim_type": str(data.get("claim_type", "implication")),
        "terminal_form": _pick(data, "terminal_form"),
        "verification_status": _pick(data, "verification_status"),
        "trust_level": _pick(data, "trust_level"),
        "provenance_type": _pick(data, "provenance_type"),
        "metadata_json": json.dumps(data.get("metadata", data), sort_keys=True),
    }


def _certificate_row(cert: Any) -> dict[str, Any]:
    data = _as_dict(cert)
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else data
    return {
        "certificate_id": str(
            _pick(data, "certificate_id", "derived_claim", "proof_id") or _warehouse_id("certificate", data)
        ),
        "claim_id": _pick(data, "claim_id", "claim", "claim_hash", "derived_claim"),
        "source_idx": _str_or_none(_pick(data, "source_idx", "source_id")),
        "target_idx": _str_or_none(_pick(data, "target_idx", "target_id")),
        "terminal_form": str(_pick(data, "terminal_form") or "NAMED_OBSTRUCTION"),
        "verification_status": str(_pick(data, "verification_status") or "UNKNOWN"),
        "trust_level": _pick(data, "trust_level"),
        "provenance_type": _pick(data, "provenance_type"),
        "derivation_rule": _pick(data, "derivation_rule"),
        "route": _pick(data, "route", "compiled_route"),
        "payload_json": json.dumps(payload, sort_keys=True),
        "evidence_json": json.dumps(data.get("evidence", {}), sort_keys=True),
    }


def _refutation_row(row: Any) -> dict[str, Any]:
    data = _as_dict(row)
    table = _pick(data, "table", "countermodel", "operation_table", "cayley_table")
    witness = _pick(data, "witness", "assignment")
    refutation_id = str(
        _pick(data, "refutation_id", "certificate_id", "derived_claim")
        or _warehouse_id("refutation", data)
    )
    return {
        "refutation_id": refutation_id,
        "claim_id": _pick(data, "claim_id", "claim", "claim_hash", "derived_claim"),
        "source": _pick(data, "source", "source_equation"),
        "target": _pick(data, "target", "target_equation"),
        "source_idx": _str_or_none(_pick(data, "source_idx", "source_id")),
        "target_idx": _str_or_none(_pick(data, "target_idx", "target_id")),
        "terminal_form": str(_pick(data, "terminal_form") or "FINITE_COUNTERMODEL"),
        "verification_status": str(
            _pick(data, "verification_status") or _pick(data, "finite_verification_status") or "FINITE_VERIFIED"
        ),
        "trust_level": str(_pick(data, "trust_level") or "FINITE_VERIFIED"),
        "provenance_type": str(_pick(data, "provenance_type") or "IMPORTED"),
        "table_hash": _pick(data, "table_hash", "seed_table_hash", "elevated_table_hash"),
        "table_name": _pick(data, "table_name", "countermodel_name"),
        "table_json": json.dumps(_jsonish(table), sort_keys=True) if table not in (None, "") else None,
        "witness_json": json.dumps(_jsonish(witness), sort_keys=True) if witness not in (None, "") else None,
        "derivation_rule": _pick(data, "derivation_rule"),
        "elevation_method": _pick(data, "elevation_method"),
        "payload_json": json.dumps(data, sort_keys=True),
    }


def _root_store_row(root: Any) -> dict[str, Any]:
    from mathgraph.root_nodes import RootNode

    data = root.to_dict() if hasattr(root, "to_dict") else RootNode.from_dict(dict(root)).to_dict()
    return {
        **{key: data.get(key) for key in (
            "root_node_id",
            "canonical_name",
            "root_type",
            "root_key",
            "table_motif",
            "algebra_shape",
            "source_target_basin",
            "forced_transition",
            "support_count",
            "rows",
            "unique_pairs",
            "unique_sources",
            "unique_targets",
            "unique_tables",
            "unique_motifs",
            "load_bearing_score",
            "status",
        )},
        "payload_json": json.dumps(data, sort_keys=True),
    }


def _reason_store_row(reason: Any) -> dict[str, Any]:
    from mathgraph.reason_nodes import ReasonNode

    data = reason.to_dict() if hasattr(reason, "to_dict") else ReasonNode.from_dict(dict(reason)).to_dict()
    return {
        **{key: data.get(key) for key in (
            "reason_node_id",
            "reason_type",
            "reason_key",
            "table_motif",
            "algebra_shape",
            "forced_transition",
            "derivation_rule",
            "support_count",
            "rows",
            "reason_score",
            "status",
        )},
        "payload_json": json.dumps(data, sort_keys=True),
    }


def _obstruction_store_row(obstruction: Any) -> dict[str, Any]:
    from mathgraph.obstruction_atlas import ObstructionNode

    data = (
        obstruction.to_dict()
        if hasattr(obstruction, "to_dict")
        else ObstructionNode.from_dict(dict(obstruction)).to_dict()
    )
    return {
        **{key: data.get(key) for key in (
            "obstruction_id",
            "obstruction_signature",
            "failure_reason",
            "derivation_rule",
            "source_target_basin",
            "forced_transition",
            "table_motif",
            "rows",
            "obstruction_pressure_score",
        )},
        "payload_json": json.dumps(data, sort_keys=True),
    }


def _root_alias_store_row(alias: Any) -> dict[str, Any]:
    data = _as_dict(alias)
    return {
        "alias": str(_pick(data, "alias", "name") or _warehouse_id("root_alias", data)),
        "root_node_id": _pick(data, "root_node_id", "root_id"),
        "canonical_name": _pick(data, "canonical_name"),
        "evidence_json": json.dumps(data.get("evidence", data), sort_keys=True),
    }


def _table_store_row(row: dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    table = _pick(data, "table", "operation_table", "cayley_table")
    return {
        "table_hash": str(_pick(data, "table_hash", "hash") or _warehouse_id("table", data)),
        "table_name": _pick(data, "table_name", "name"),
        "table_json": json.dumps(_jsonish(table), sort_keys=True) if table not in (None, "") else None,
        "motif": _pick(data, "motif", "table_motif"),
        "algebra_shape": _pick(data, "algebra_shape"),
        "payload_json": json.dumps(data, sort_keys=True),
    }


def _claim_record(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    return {
        **data,
        "status": "hit",
        "metadata": json.loads(data["metadata_json"]),
    }


def _refutation_record(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    return {
        **data,
        "status": "hit",
        "table": json.loads(data["table_json"]) if data.get("table_json") else None,
        "witness": json.loads(data["witness_json"]) if data.get("witness_json") else None,
        "payload": json.loads(data["payload_json"]),
    }


def _root_store_record(row: sqlite3.Row) -> dict[str, Any]:
    return json.loads(dict(row)["payload_json"])


def _reason_store_record(row: sqlite3.Row) -> dict[str, Any]:
    return json.loads(dict(row)["payload_json"])


def _obstruction_store_record(row: sqlite3.Row) -> dict[str, Any]:
    return json.loads(dict(row)["payload_json"])


def _domain_kernel_record(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    return {
        "kernel_id": data["kernel_id"],
        "name": data["name"],
        "description": data["description"],
        "native_language": data["native_language"],
        "host_verifier": data["host_verifier"],
        "embedding_kind": data["embedding_kind"],
        "source_uri": data["source_uri"],
        "source_commit": data["source_commit"],
        "trust_policy": data["trust_policy"],
        "ontology_summary": json.loads(data["ontology_summary_json"]),
        "metadata": json.loads(data["metadata_json"]),
        "host_logic": data.get("host_logic") or "",
        "object_logic": data.get("object_logic") or "",
        "object_theory": data.get("object_theory") or "",
        "artifact_risk": data.get("artifact_risk") or "UNKNOWN",
        "proof_transport_status": data.get("proof_transport_status") or "NOT_ATTEMPTED",
        "default_denotation_policy": data.get("default_denotation_policy") or "",
        "default_type_system": data.get("default_type_system") or "",
        "default_identity_policy": data.get("default_identity_policy") or "",
        "default_hyperintensional_identity_policy": data.get("default_hyperintensional_identity_policy") or "",
        "extensional_collapse_policy": data.get("extensional_collapse_policy") or "NEVER_BY_DEFAULT",
        "workbench_id": data.get("workbench_id") or "",
        "workbench_layer": data.get("workbench_layer") or "",
        "lifecycle_status": data.get("lifecycle_status") or "",
        "embedding_strategy": data.get("embedding_strategy") or "",
        "faithfulness_status": data.get("faithfulness_status") or "",
        "benchmark_status": data.get("benchmark_status") or "",
        "default_formal_world_id": data.get("default_formal_world_id") or "",
        "notes": data.get("notes") or "",
        "created_at": data["created_at"],
        "advisory_only": True,
        "truth_boundary": "DomainKernel registration is metadata, not verification.",
    }


def _filters(values: dict[str, Any]) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    for key, value in values.items():
        if value is not None:
            clauses.append(f"{key} = ?")
            params.append(value)
    return clauses, params


def _payload_record(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    payload = json.loads(data.pop("payload_json", "{}") or "{}")
    data["payload"] = payload
    data["advisory_only"] = True
    return data


def _json_columns_record(row: sqlite3.Row) -> dict[str, Any]:
    data = _payload_record(row)
    for key in list(data):
        if key.endswith("_json"):
            decoded_key = key[:-5]
            try:
                data[decoded_key] = json.loads(data.pop(key) or "null")
            except json.JSONDecodeError:
                pass
    return data


def _typed_object_record(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["encoded_properties"] = json.loads(data.pop("encoded_properties_json") or "{}")
    data["exemplified_properties"] = json.loads(data.pop("exemplified_properties_json") or "{}")
    data["payload"] = json.loads(data.pop("payload_json") or "{}")
    data["advisory_only"] = True
    return data


def _semantic_embedding_record(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["metadata"] = json.loads(data.pop("metadata_json") or "{}")
    payload_json = data.pop("payload_json", None)
    data["payload"] = json.loads(payload_json) if payload_json else {}
    data["object_theory_verified"] = bool(data.get("object_theory_verified"))
    data["host_embedding_verified"] = bool(data.get("host_embedding_verified"))
    faithfulness_validated = bool(data.get("faithfulness_assessment_id")) or bool(
        data.get("payload", {}).get("faithfulness_validated")
    )
    native = data.get("embedding_kind") in {"NATIVE_KERNEL", "DIRECT_NATIVE"}
    data["advisory_only"] = not (
        data.get("object_theory_verified")
        and data.get("artifact_risk") in {"NONE", "LOW"}
        and (native or (data.get("proof_transport_status") == "TRANSPORT_VALIDATED" and faithfulness_validated))
    )
    return data


def _as_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if isinstance(value, dict):
        return dict(value)
    return dict(vars(value))


def _pick(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _normalize_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return " ".join(str(value).strip().split())


def _str_or_none(value: Any) -> str | None:
    return None if value in (None, "") else str(value)


def _jsonish(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _sql_value(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return value.value if hasattr(value, "value") else value


def _row_id(row: Any, key: str) -> str:
    data = _as_dict(row)
    return str(data.get(key, ""))


def _warehouse_id(kind: str, data: dict[str, Any]) -> str:
    from mathgraph.hashing import content_id

    return content_id(kind, data)


def _trace_value(trace: Trace, key: str) -> str | None:
    for payload in _payloads(trace):
        value = _nested_value(payload, key)
        if value is not None:
            return str(value)
    return None


def _payloads(trace: Trace) -> list[dict[str, Any]]:
    payloads = [trace.metadata]
    if trace.certificate is not None:
        payloads.append(trace.certificate.payload)
    if trace.obstruction is not None:
        payloads.append(trace.obstruction.payload)
    return [payload for payload in payloads if isinstance(payload, dict)]


def _nested_value(payload: dict[str, Any], key: str) -> Any:
    if key in payload and payload[key] not in (None, ""):
        return payload[key]
    for nested_key in ("model", "record"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict) and nested.get(key) not in (None, ""):
            return nested.get(key)
    return None


# -------------------------------------------------------------------------------------------------
# Compounding Lawbook Engine v0 surface
# -------------------------------------------------------------------------------------------------

_VERIFIED_TERMINAL_BOUNDARIES = {
    "VERIFIED_PROOF": {"lean", "proof_checker", "derived_verified"},
    "FINITE_COUNTERMODEL": {"finite_model_checker", "derived_verified"},
    "NAMED_OBSTRUCTION": {"obstruction_audit", "derived_obstruction"},
}


def _lb_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _lb_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, sort_keys=True, ensure_ascii=False)


def _lb_hash(value: Any) -> str:
    from mathgraph.hashing import content_id

    return content_id("lawbook-v0", value)


def _validate_terminal_boundary(terminal_form: str, boundary_type: str, trust_level: int) -> None:
    if terminal_form in ("", "ADVISORY", "CANDIDATE", "NONE"):
        return
    allowed = _VERIFIED_TERMINAL_BOUNDARIES.get(str(terminal_form), set())
    if str(boundary_type) not in allowed:
        raise ValueError(f"{terminal_form} requires boundary_type in {sorted(allowed)}")
    if int(trust_level) < 100:
        raise ValueError(f"{terminal_form} requires verified trust_level >= 100")


def _init_compounding_schema(self: LawbookStore) -> None:
    self.conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS artifacts (
            artifact_id TEXT PRIMARY KEY,
            domain TEXT,
            claim_id TEXT,
            source_id TEXT,
            target_id TEXT,
            basin TEXT,
            micro_basin TEXT,
            terminal_form TEXT,
            trust_level INTEGER,
            provenance_type TEXT,
            boundary_type TEXT,
            payload_json TEXT,
            payload_hash TEXT,
            run_id TEXT,
            created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_artifacts_domain ON artifacts(domain);
        CREATE INDEX IF NOT EXISTS idx_artifacts_claim ON artifacts(claim_id);
        CREATE INDEX IF NOT EXISTS idx_artifacts_pair ON artifacts(source_id, target_id);
        CREATE INDEX IF NOT EXISTS idx_artifacts_basin ON artifacts(basin);
        CREATE INDEX IF NOT EXISTS idx_artifacts_terminal ON artifacts(terminal_form);

        CREATE TABLE IF NOT EXISTS attempts (
            attempt_id TEXT PRIMARY KEY,
            artifact_id TEXT,
            domain TEXT,
            claim_id TEXT,
            route TEXT,
            scheduler TEXT,
            result_type TEXT,
            success INTEGER,
            cost REAL,
            residual_delta REAL,
            verifier_contact INTEGER,
            run_id TEXT,
            created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_attempts_claim ON attempts(claim_id);
        CREATE INDEX IF NOT EXISTS idx_attempts_route ON attempts(route);
        CREATE INDEX IF NOT EXISTS idx_attempts_success ON attempts(success);

        CREATE TABLE IF NOT EXISTS compounding_obstructions (
            obstruction_id TEXT PRIMARY KEY,
            domain TEXT,
            claim_id TEXT,
            source_id TEXT,
            target_id TEXT,
            basin TEXT,
            obstruction_type TEXT,
            evidence_json TEXT,
            route_killed TEXT,
            run_id TEXT,
            created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_compounding_obstructions_basin ON compounding_obstructions(basin);

        CREATE TABLE IF NOT EXISTS compounding_reasons (
            reason_id TEXT PRIMARY KEY,
            domain TEXT,
            reason_type TEXT,
            basin TEXT,
            support_count INTEGER,
            verified_support_count INTEGER,
            conditions_json TEXT,
            payload_json TEXT,
            promotion_status TEXT,
            decode_success_count INTEGER,
            decode_failure_count INTEGER,
            run_id TEXT,
            created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_compounding_reasons_basin ON compounding_reasons(basin);
        CREATE INDEX IF NOT EXISTS idx_compounding_reasons_status ON compounding_reasons(promotion_status);

        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT,
            payload_json TEXT,
            run_id TEXT,
            created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
        """
    )
    self.conn.commit()


def _insert_artifact(self: LawbookStore, artifact: dict[str, Any]) -> dict[str, Any]:
    self.init_compounding_schema()
    payload = dict(artifact.get("payload", artifact.get("payload_json", {})) or {})
    artifact_id = str(artifact.get("artifact_id") or _lb_hash(["artifact", artifact]))
    terminal = str(artifact.get("terminal_form", "ADVISORY") or "ADVISORY")
    boundary = str(artifact.get("boundary_type", "") or "")
    trust = int(artifact.get("trust_level", 0) or 0)
    _validate_terminal_boundary(terminal, boundary, trust)
    row = {
        "artifact_id": artifact_id,
        "domain": artifact.get("domain", ""),
        "claim_id": artifact.get("claim_id", ""),
        "source_id": artifact.get("source_id", ""),
        "target_id": artifact.get("target_id", ""),
        "basin": artifact.get("basin", ""),
        "micro_basin": artifact.get("micro_basin", ""),
        "terminal_form": terminal,
        "trust_level": trust,
        "provenance_type": artifact.get("provenance_type", ""),
        "boundary_type": boundary,
        "payload_json": _lb_json(payload),
        "payload_hash": artifact.get("payload_hash") or _lb_hash(payload),
        "run_id": artifact.get("run_id", ""),
        "created_at": artifact.get("created_at") or _lb_now(),
    }
    self.conn.execute(
        "INSERT OR REPLACE INTO artifacts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        tuple(row[k] for k in row),
    )
    self.conn.commit()
    return row


def _insert_attempt(self: LawbookStore, attempt: dict[str, Any]) -> dict[str, Any]:
    self.init_compounding_schema()
    row = {
        "attempt_id": str(attempt.get("attempt_id") or _lb_hash(["attempt", attempt])),
        "artifact_id": attempt.get("artifact_id", ""),
        "domain": attempt.get("domain", ""),
        "claim_id": attempt.get("claim_id", ""),
        "route": attempt.get("route", ""),
        "scheduler": attempt.get("scheduler", ""),
        "result_type": attempt.get("result_type", ""),
        "success": 1 if attempt.get("success") else 0,
        "cost": float(attempt.get("cost", 0.0) or 0.0),
        "residual_delta": float(attempt.get("residual_delta", 0.0) or 0.0),
        "verifier_contact": 1 if attempt.get("verifier_contact") else 0,
        "run_id": attempt.get("run_id", ""),
        "created_at": attempt.get("created_at") or _lb_now(),
    }
    self.conn.execute("INSERT OR REPLACE INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(row[k] for k in row))
    self.conn.commit()
    return row


def _insert_obstruction(self: LawbookStore, obstruction: dict[str, Any]) -> dict[str, Any]:
    self.init_compounding_schema()
    row = {
        "obstruction_id": str(obstruction.get("obstruction_id") or _lb_hash(["obstruction", obstruction])),
        "domain": obstruction.get("domain", ""),
        "claim_id": obstruction.get("claim_id", ""),
        "source_id": obstruction.get("source_id", ""),
        "target_id": obstruction.get("target_id", ""),
        "basin": obstruction.get("basin", ""),
        "obstruction_type": obstruction.get("obstruction_type", ""),
        "evidence_json": _lb_json(obstruction.get("evidence", obstruction.get("evidence_json", {}))),
        "route_killed": obstruction.get("route_killed", ""),
        "run_id": obstruction.get("run_id", ""),
        "created_at": obstruction.get("created_at") or _lb_now(),
    }
    self.conn.execute("INSERT OR REPLACE INTO compounding_obstructions VALUES (?,?,?,?,?,?,?,?,?,?,?)", tuple(row[k] for k in row))
    self.conn.commit()
    return row


def _insert_reason(self: LawbookStore, reason: dict[str, Any]) -> dict[str, Any]:
    self.init_compounding_schema()
    status = str(reason.get("promotion_status", "CANDIDATE_REASON") or "CANDIDATE_REASON")
    if status == "LAWBOOK_REASON" and int(reason.get("decode_success_count", 0) or 0) <= 0:
        raise ValueError("LAWBOOK_REASON requires decode_success_count > 0")
    row = {
        "reason_id": str(reason.get("reason_id") or _lb_hash(["reason", reason])),
        "domain": reason.get("domain", ""),
        "reason_type": reason.get("reason_type", ""),
        "basin": reason.get("basin", ""),
        "support_count": int(reason.get("support_count", 0) or 0),
        "verified_support_count": int(reason.get("verified_support_count", 0) or 0),
        "conditions_json": _lb_json(reason.get("conditions", reason.get("conditions_json", {}))),
        "payload_json": _lb_json(reason.get("payload", reason.get("payload_json", {}))),
        "promotion_status": status,
        "decode_success_count": int(reason.get("decode_success_count", 0) or 0),
        "decode_failure_count": int(reason.get("decode_failure_count", 0) or 0),
        "run_id": reason.get("run_id", ""),
        "created_at": reason.get("created_at") or _lb_now(),
    }
    self.conn.execute("INSERT OR REPLACE INTO compounding_reasons VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(row[k] for k in row))
    self.conn.commit()
    return row


def _insert_event(self: LawbookStore, event: dict[str, Any]) -> dict[str, Any]:
    self.init_compounding_schema()
    row = {
        "event_id": str(event.get("event_id") or _lb_hash(["event", event, _lb_now()])),
        "event_type": event.get("event_type", ""),
        "payload_json": _lb_json(event.get("payload", event.get("payload_json", {}))),
        "run_id": event.get("run_id", ""),
        "created_at": event.get("created_at") or _lb_now(),
    }
    self.conn.execute("INSERT OR REPLACE INTO events VALUES (?,?,?,?,?)", tuple(row[k] for k in row))
    self.conn.commit()
    return row


def _query_artifacts(self: LawbookStore, **kwargs: Any) -> list[dict[str, Any]]:
    self.init_compounding_schema()
    fields = ("domain", "claim_id", "source_id", "target_id", "basin", "micro_basin", "terminal_form")
    clauses = []
    params = []
    for field in fields:
        value = kwargs.get(field)
        if value not in (None, ""):
            clauses.append(f"{field}=?")
            params.append(str(value))
    sql = "SELECT * FROM artifacts"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY trust_level DESC, created_at DESC LIMIT ?"
    params.append(int(kwargs.get("limit", 100) or 100))
    return [_json_columns_record(row) for row in self.conn.execute(sql, params).fetchall()]


def _query_compounding_reasons(self: LawbookStore, *, domain: str | None = None, basin: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    self.init_compounding_schema()
    clauses = []
    params = []
    if domain:
        clauses.append("domain=?")
        params.append(domain)
    if basin:
        clauses.append("basin=?")
        params.append(basin)
    sql = "SELECT * FROM compounding_reasons"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY verified_support_count DESC, support_count DESC LIMIT ?"
    params.append(limit)
    return [_json_columns_record(row) for row in self.conn.execute(sql, params).fetchall()]


def _query_compounding_obstructions(self: LawbookStore, *, domain: str | None = None, basin: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    self.init_compounding_schema()
    clauses = []
    params = []
    if domain:
        clauses.append("domain=?")
        params.append(domain)
    if basin:
        clauses.append("basin=?")
        params.append(basin)
    sql = "SELECT * FROM compounding_obstructions"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return [_json_columns_record(row) for row in self.conn.execute(sql, params).fetchall()]


def _retrieve_candidate_context(self: LawbookStore, task: dict[str, Any], max_artifacts: int = 5, max_obstructions: int = 5, max_reasons: int = 5) -> dict[str, Any]:
    domain = task.get("domain", "sair")
    basin = task.get("basin") or task.get("family", "")
    return {
        "artifacts": self.query_artifacts(domain=domain, basin=basin, limit=max_artifacts),
        "obstructions": self.query_compounding_obstructions(domain=domain, basin=basin, limit=max_obstructions),
        "reasons": self.query_compounding_reasons(domain=domain, basin=basin, limit=max_reasons),
    }


def _export_manifest(self: LawbookStore, path: str | Path) -> dict[str, Any]:
    self.init_compounding_schema()
    manifest = {
        "artifacts": self.conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0],
        "attempts": self.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0],
        "obstructions": self.conn.execute("SELECT COUNT(*) FROM compounding_obstructions").fetchone()[0],
        "reasons": self.conn.execute("SELECT COUNT(*) FROM compounding_reasons").fetchone()[0],
        "events": self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
        "advisory_boundary_preserved": self.conn.execute("SELECT COUNT(*) FROM artifacts WHERE terminal_form IN ('VERIFIED_PROOF','FINITE_COUNTERMODEL','NAMED_OBSTRUCTION') AND trust_level < 100").fetchone()[0] == 0,
    }
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


LawbookStore.init_compounding_schema = _init_compounding_schema  # type: ignore[attr-defined]
LawbookStore.insert_artifact = _insert_artifact  # type: ignore[attr-defined]
LawbookStore.insert_attempt = _insert_attempt  # type: ignore[attr-defined]
LawbookStore.insert_obstruction = _insert_obstruction  # type: ignore[attr-defined]
LawbookStore.insert_reason = _insert_reason  # type: ignore[attr-defined]
LawbookStore.insert_event = _insert_event  # type: ignore[attr-defined]
LawbookStore.query_artifacts = _query_artifacts  # type: ignore[attr-defined]
LawbookStore.query_compounding_reasons = _query_compounding_reasons  # type: ignore[attr-defined]
LawbookStore.query_compounding_obstructions = _query_compounding_obstructions  # type: ignore[attr-defined]
LawbookStore.retrieve_candidate_context = _retrieve_candidate_context  # type: ignore[attr-defined]
LawbookStore.export_manifest = _export_manifest  # type: ignore[attr-defined]
