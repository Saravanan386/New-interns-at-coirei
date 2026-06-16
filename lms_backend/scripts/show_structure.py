from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {".git", "__pycache__", "venv", ".venv", ".idea", ".vscode", "node_modules"}


def print_tree(path: Path, prefix: str = "", max_depth: int | None = None, current_depth: int = 0) -> None:
    if max_depth is not None and current_depth > max_depth:
        return

    entries = sorted(
        [entry for entry in path.iterdir() if entry.name not in EXCLUDE_DIRS],
        key=lambda entry: (entry.is_file(), entry.name.lower()),
    )

    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        print(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if index == len(entries) - 1 else "│   "
            print_tree(entry, prefix + extension, max_depth, current_depth + 1)


def find_router_prefixes(router_dir: Path) -> list[tuple[str, str]]:
    prefixes: list[tuple[str, str]] = []
    for path in sorted(router_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"APIRouter\([^\)]*prefix\s*=\s*[\"']([^\"']+)[\"']", text)
        if match:
            prefixes.append((path.name, match.group(1)))
        else:
            prefixes.append((path.name, "(no explicit prefix)"))
    return prefixes


def print_summary() -> None:
    print("\n=== Docker database summary ===")
    print("Compose files: docker-compose.demo.yml, docker-compose.full-demo.yml")
    print("Environment file: .env.demo")
    print("Database service: postgres:18-alpine")
    print("Named volume: postgres_data")
    print("Backend service uses DATABASE_URL pointing at db:5432")
    print("Suggested start command:")
    print("  docker compose --env-file .env.demo -f docker-compose.demo.yml up -d --build")

    print("\n=== FastAPI entrypoint ===")
    print("Main app file: app/main.py")
    print("Health check: GET /health")
    print("API docs: GET /docs and GET /redoc")

    router_dir = ROOT / "app" / "routers"
    if router_dir.exists():
        prefixes = find_router_prefixes(router_dir)
        print("\n=== Router prefixes found in app/routers ===")
        for name, prefix in prefixes:
            print(f"  {name}: {prefix}")
    else:
        print("Warning: app/routers directory not found.")


def main() -> None:
    print("Project structure for lms_backend:")
    print(f"Root: {ROOT}")
    print_tree(ROOT)
    print_summary()


if __name__ == "__main__":
    main()
