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
            """
        )
        self.conn.commit()

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
            )
        }
        cert_rows = [dict(row) for row in self.conn.execute("SELECT terminal_form FROM certificates")]
        return {
            **counts,
            "certificate_terminal_form_counts": dict(Counter(row["terminal_form"] for row in cert_rows)),
        }

    def summary(self) -> dict[str, Any]:
        return {
            "primitive": self.stats().to_dict(),
            "derived": self.derived_stats(),
            "warehouse": self.warehouse_summary(),
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
