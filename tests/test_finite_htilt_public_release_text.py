from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "releases" / "finite_htilt_theorem_tower_v1"
GITHUB_BODY = RELEASE / "GITHUB_RELEASE_BODY.md"
ANNOUNCEMENT = RELEASE / "public_announcement.md"
SOCIAL = RELEASE / "social_snippets.md"
CHECKLIST = RELEASE / "post_release_visibility_checklist.md"
NEXT_ISSUE = ROOT / "issues" / "killed_generator_bridge_from_discrete_pf.md"
RELEASE_INDEX = ROOT / "docs" / "release_index.md"

PUBLIC_TEXT_FILES = (GITHUB_BODY, ANNOUNCEMENT, SOCIAL, CHECKLIST)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_public_release_files_exist() -> None:
    for path in (*PUBLIC_TEXT_FILES, NEXT_ISSUE):
        assert path.is_file(), path


def test_github_release_body_covers_all_three_layers() -> None:
    text = _read(GITHUB_BODY)
    for layer in ("Layer 1", "Layer 2", "Layer 3"):
        assert layer in text
    for artifact in (
        "finite_htilt_survivor_law_v1.json",
        "finite_htilt_discrete_doob_stationary_v1.json",
        "finite_htilt_pf_discrete_survivor_law_v1.json",
    ):
        assert artifact in text


def test_github_release_body_records_precise_trust_boundary() -> None:
    text = _read(GITHUB_BODY)
    normalized = " ".join(text.split())
    assert "no `sorryAx` dependency" in text
    assert "external PF subtree contains one unrelated `sorry`" in text
    assert "clean dependency graph for the promoted theorem" in normalized
    assert "not global placeholder-freedom" in normalized


def test_public_announcement_contains_mathgraph_loop() -> None:
    text = _read(ANNOUNCEMENT)
    for stage in (
        "speculative theory",
        "claim decomposition",
        "exact kernel extraction",
        "Lean verification",
        "external theorem portal",
        "Lawbook",
        "release tag",
        "explicit non-claims",
    ):
        assert stage in text


def test_social_snippets_preserve_bounded_nonclaims() -> None:
    text = _read(SOCIAL).lower()
    for boundary in (
        "no killed-generator bridge",
        "no convergence",
        "consciousness",
        "scheduler",
    ):
        assert boundary in text


def test_next_issue_is_bounded_draft_text() -> None:
    text = _read(NEXT_ISSUE)
    assert "## Definition of done" in text
    assert "## Kill condition" in text
    assert "issue draft text only" in text
    assert "No GitHub issue has been created" in text


def test_public_release_text_avoids_forbidden_overclaims() -> None:
    text = "\n".join(_read(path) for path in PUBLIC_TEXT_FILES).lower()
    for forbidden in (
        "proves consciousness",
        "proves h-band universality",
        "proves scheduler performance",
        "proves markov convergence",
        "proves killed-generator pf existence",
        "solves consciousness",
        "universal h-band",
    ):
        assert forbidden not in text


def test_release_index_links_to_release_bundle() -> None:
    assert RELEASE_INDEX.is_file()
    assert "releases/finite_htilt_theorem_tower_v1/" in _read(RELEASE_INDEX)


def test_readme_link_is_checked_if_present() -> None:
    readme = _read(ROOT / "README.md")
    if "finite-htilt-theorem-tower-v1" in readme:
        assert "releases/finite_htilt_theorem_tower_v1/" in readme
