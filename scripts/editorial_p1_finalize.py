# -*- coding: utf-8 -*-
"""Fecha a passada P1: remove fillers fracos e corrige resíduos gramaticais."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from editorial_p1 import expand_fillers, norm  # noqa: E402

SEED = ROOT / "src" / "main" / "resources" / "seed"
LEVELS = {1: 150, 2: 100, 3: 250}

REWRITES = {
    "O que agrupa classes em um namespace lógico?": "O que um pacote faz em Java?",
    "O que referencia a instância atual?": "O que a palavra-chave this referencia?",
    "O que classe/método incompleto que exige implementação?": "O que caracteriza um método abstrato?",
    "O que referencia a superclasse?": "O que a palavra-chave super referencia?",
    "O que Anotação @Deprecated indica?": "O que a anotação @Deprecated indica?",
    "O que referencia variável de escopo enclosing?": "O que a palavra-chave nonlocal referencia?",
    "O que optional[X] significa?": "O que Optional[X] significa em type hints?",
    "O que @staticmethod não recebe?": "O que um @staticmethod não recebe automaticamente?",
    "O que @classmethod recebe tipicamente?": "O que um @classmethod recebe tipicamente como primeiro argumento?",
    "O que __enter__/__exit__ compõem?": "O que os métodos __enter__/__exit__ compõem?",
    "O que agrupa nomes para evitar colisões?": "O que um namespace faz em C++?",
    "O que Vector::push_back faz?": "O que std::vector::push_back faz?",
    "O que enumeração tipa da/escopada?": "O que caracteriza um enum class?",
    "O que Std::set armazena?": "O que std::set armazena?",
    "O que Std::map armazena?": "O que std::map armazena?",
    "O que String::size retorna?": "O que std::string::size retorna?",
    "O que Try/catch trata?": "O que um bloco try/catch trata?",
    "O que Std::move faz?": "O que std::move faz?",
    "Qual opção completa corretamente a ideia: Stream.map faz o quê?": "O que Stream.map faz?",
    "Qual opção completa corretamente a ideia: Stream.filter faz o quê?": "O que Stream.filter faz?",
}


def is_weak(e: str) -> bool:
    el = e.lower()
    if "corresponde ao conceito" in el:
        return True
    if re.search(r"\bitem \d+", el):
        return True
    if "o que é o caracteriza" in el or "o que é a caracteriza" in el:
        return True
    return False


def fix_enunciado(e: str) -> str:
    for src, dst in REWRITES.items():
        if norm(src) == norm(e):
            e = dst
            break
    e = re.sub(
        r"(?i)^Qual opção completa corretamente a ideia:\s*(.+?)\s+faz o qu[eê]\?\s*$",
        r"O que \1 faz?",
        e,
    )
    e = re.sub(
        r"(?i)^O que é (o|a)\s+(caracteriza|verifica|remove|impede|introduz|nomeia)\s+(.+)$",
        r"O que \2 \3",
        e,
    )
    e = re.sub(r"\s+", " ", e).strip()
    if e and not e.endswith("?"):
        e += "?"
    if e:
        e = e[0].upper() + e[1:]
    return e


def process(lang: str) -> dict:
    path = SEED / f"perguntas-{lang}.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    used: set[str] = set()
    by: dict[int, list] = {1: [], 2: [], 3: []}
    removed_weak = 0
    fixed = 0

    for p in data:
        old = p["enunciado"]
        e = fix_enunciado(old)
        if e != old:
            fixed += 1
        if is_weak(e):
            removed_weak += 1
            continue
        k = norm(e)
        if k in used:
            continue
        used.add(k)
        by[int(p["dificuldade"])].append({**p, "enunciado": e})

    added = {1: 0, 2: 0, 3: 0}
    for dif, quota in LEVELS.items():
        if len(by[dif]) > quota:
            by[dif] = by[dif][:quota]
        elif len(by[dif]) < quota:
            need = quota - len(by[dif])
            # expand_fillers já evita colisões via `used` e registra as chaves
            extra = expand_fillers(lang, dif, need, used)
            for q in extra:
                q["enunciado"] = fix_enunciado(q["enunciado"])
                if is_weak(q["enunciado"]):
                    continue
                k = norm(q["enunciado"])
                # pode colidir só se o fix reescrever para enunciado já existente
                if k in {norm(x["enunciado"]) for x in by[1] + by[2] + by[3]}:
                    continue
                used.add(k)
                by[dif].append(q)
            # completa o que faltou por colisão pós-fix
            guard = 0
            while len(by[dif]) < quota and guard < 500:
                guard += 1
                more = expand_fillers(lang, dif, quota - len(by[dif]), used)
                progressed = False
                for q in more:
                    q["enunciado"] = fix_enunciado(q["enunciado"])
                    if is_weak(q["enunciado"]):
                        continue
                    k = norm(q["enunciado"])
                    existing = {norm(x["enunciado"]) for x in by[1] + by[2] + by[3]}
                    if k in existing:
                        continue
                    used.add(k)
                    by[dif].append(q)
                    progressed = True
                    if len(by[dif]) >= quota:
                        break
                if not progressed:
                    break
            added[dif] = need
            by[dif] = by[dif][:quota]

    final = by[1] + by[2] + by[3]
    path.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sobre = sum(1 for p in final if p["enunciado"].lower().startswith("sobre "))
    resulta = sum(1 for p in final if re.search(r"(?i)resulta em\?", p["enunciado"]))
    weak = sum(1 for p in final if is_weak(p["enunciado"]))
    mangled = sum(1 for p in final if re.search(r"(?i)o que é (o|a) caracteriza", p["enunciado"]))
    return {
        "lang": lang,
        "fixed": fixed,
        "removed_weak": removed_weak,
        "added": added,
        "total": len(final),
        "by_level": {d: len(by[d]) for d in LEVELS},
        "unique": len({norm(p["enunciado"]) for p in final}),
        "sobre": sobre,
        "resulta": resulta,
        "weak": weak,
        "mangled": mangled,
    }


def main() -> None:
    print(json.dumps([process(l) for l in ("java", "python", "cpp")], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
