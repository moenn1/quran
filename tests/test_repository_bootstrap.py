from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_monorepo_placeholders_exist() -> None:
    expected_paths = [
        ROOT / "apps" / "api" / "README.md",
        ROOT / "apps" / "cli" / "README.md",
        ROOT / "apps" / "web",
        ROOT / "packages" / "database" / "README.md",
        ROOT / "packages" / "embeddings" / "README.md",
        ROOT / "packages" / "shared" / "README.md",
        ROOT / "data" / "README.md",
        ROOT / "docs" / "architecture.md",
    ]

    missing = [path.relative_to(ROOT).as_posix() for path in expected_paths if not path.exists()]

    assert not missing, f"Missing required repository bootstrap paths: {missing}"


def test_architecture_note_covers_recommended_stack() -> None:
    architecture_note = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")

    for keyword in ("FastAPI", "Typer", "Next.js", "PostgreSQL", "Qdrant"):
        assert keyword in architecture_note

    assert "textual similarity only" in architecture_note
