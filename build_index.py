"""Executa o indexador existente sem duplicar ou alterar sua implementação."""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
INDEXER_DIR = ROOT_DIR / "database"


def build_index() -> None:
    """Gera o índice executando database/create_db.py no diretório esperado."""
    subprocess.run(
        [sys.executable, "create_db.py"],
        cwd=INDEXER_DIR,
        check=True,
    )


if __name__ == "__main__":
    build_index()