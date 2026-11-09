#!/usr/bin/env python3
"""
Os bancos oficiais ficam em src/main/resources/seed/perguntas-*.json.

Para regenerar/enxugar enunciados mal formulados, use:
    python scripts/limpar_enunciados.py
"""

from __future__ import annotations

import sys


def main() -> None:
    print(
        "Os JSONs de perguntas já estão em src/main/resources/seed/.\n"
        "Para corrigir enunciados, execute: python scripts/limpar_enunciados.py"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
