#!/usr/bin/env python3
"""Terceira passada: elimina resíduos ainda vagos/incompletos."""

from __future__ import annotations

import json
import re
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "src" / "main" / "resources" / "seed"


def q(texto: str) -> str:
    texto = " ".join(texto.split()).strip().rstrip(" .;:?")
    if not texto:
        return "?"
    texto = texto[0].upper() + texto[1:]
    return texto + "?"


def fix(e: str) -> str:
    e = " ".join(e.split()).strip()

    # Using namespace std
    if re.search(r"using namespace std", e, re.I):
        return q("O que a diretiva `using namespace std;` disponibiliza no código")

    # cout << "Hi"
    if "cout" in e.lower() and "hi" in e.lower():
        return q('O que o código `std::cout << "Hi";` imprime na tela')

    # Auto x = 1; infere
    if re.search(r"auto\s+x\s*=\s*1", e, re.I):
        return q("Dado o código `auto x = 1;`, qual tipo é inferido para x")

    # índices de array começam em
    if re.search(r"índices de array começam em", e, re.I):
        return q("Em um array, a partir de qual número começam os índices")

    # \n versus endl
    if "endl" in e.lower() and ("\\n" in e or "'\\n'" in e or "\n" in e):
        return q("Qual a diferença entre usar `\\n` e `std::endl`")

    # Virtual ~Base()
    if re.search(r"virtual\s*~", e, re.I):
        return q("Por que é importante declarar um destrutor virtual na classe base")

    # const int* p
    if re.search(r"const\s+int\s*\*\s*p", e, re.I):
        return q("O que significa a declaração `const int* p`")

    # int* const p
    if re.search(r"int\s*\*\s*const\s*p", e, re.I):
        return q("O que significa a declaração `int* const p`")

    # smart pointers ajudam
    if re.search(r"smart pointers?", e, re.I):
        return q("Para que servem os smart pointers")

    # vector.at(i) difere
    if re.search(r"vector\.at", e, re.I):
        return q("Qual a diferença entre `vector.at(i)` e `vector[i]`")

    # X aponta para?
    m = re.match(r"^(.+?)\s+aponta para\??$", e, flags=re.I)
    if m:
        return q(f"Para onde aponta {m.group(1).strip()}")

    # X é importante para?
    m = re.match(r"^(.+?)\s+(é importante para|importa para)\??$", e, flags=re.I)
    if m:
        return q(f"Por que {m.group(1).strip()} é importante")

    # X ajudam a evitar?
    m = re.match(r"^(.+?)\s+ajudam? a evitar\??$", e, flags=re.I)
    if m:
        return q(f"O que {m.group(1).strip()} ajudam a evitar")

    # X difere de Y porque?
    m = re.match(r"^(.+?)\s+difere de\s+(.+?)\s+porque\??$", e, flags=re.I)
    if m:
        return q(f"Por que {m.group(1).strip()} difere de {m.group(2).strip()}")

    # Sobre X versus Y, ...
    m = re.match(r"^Sobre\s+(.+?)\s+versus\s+(.+?),\s*(.+)\??$", e, flags=re.I)
    if m:
        return q(f"Qual a diferença entre {m.group(1).strip()} e {m.group(2).strip()}")

    # O que <código>; <verbo>?
    m = re.match(r"^O que\s+(.+;)\s+(disponibiliza|imprime|infere)\??$", e, flags=re.I)
    if m:
        verbo = m.group(2).lower()
        codigo = m.group(1).strip()
        if verbo == "disponibiliza":
            return q(f"O que a instrução `{codigo}` disponibiliza")
        if verbo == "imprime":
            return q(f"O que o código `{codigo}` imprime")
        if verbo == "infere":
            return q(f"Dado o código `{codigo}`, qual tipo é inferido")

    # termina com "para?" / "em?" / "porque?" incompleto
    if re.search(r"\b(para|em|porque)\??$", e, re.I) and not re.match(
        r"^(Qual|Como|Para que|O que|Dado|Quais|Quando|Em qual|Por que)\b", e, re.I
    ):
        base = re.sub(r"\s+(para|em|porque)\??$", "", e, flags=re.I).strip()
        return q(f"Qual a função de {base}")

    # Já bom
    if re.match(r"^(Qual|Como|Para que|O que|Dado|Quais|Quando|Em qual|Por que)\b", e, re.I):
        return q(e) if not e.endswith("?") else e

    return q(e)


def ainda_vaga(e: str) -> bool:
    e = e.strip()
    if re.search(r"\b(ocorre ao|serve para|comum para)\??$", e, re.I):
        return True
    if re.match(r"^(O comando|Um |Uma |Break |Continue )\b", e, re.I) and len(e.split()) <= 6:
        return True
    if re.match(r"^[A-Za-z_:<>(\)./=+\-]+\??$", e):
        return True
    if not re.match(r"^(Qual|Como|Para que|O que|Dado|Quais|Quando|Em qual|Por que)\b", e, re.I):
        if len(e.split()) <= 6:
            return True
        if re.search(r"\b(faz|é|tem|traz|para|em|porque)\??$", e, re.I):
            return True
    return False


def main() -> None:
    left = 0
    for path in sorted(SEED.glob("perguntas-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            item["enunciado"] = fix(item["enunciado"])
            if ainda_vaga(item["enunciado"]):
                left += 1
                print("ainda:", path.name, item["enunciado"])
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(path.name, "ok")
    print("restantes vagas:", left)


if __name__ == "__main__":
    main()
