from pathlib import Path


def get_project_root() -> Path:
    """Find the project root by searching upward for pyproject.toml or flake.nix."""
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / "pyproject.toml").exists() or (parent / "flake.nix").exists():
            return parent
    return Path.cwd()
