#!/usr/bin/env python3
"""Garante 4 alternativas distintas e úteis em cada pergunta do seed."""

from __future__ import annotations

import json
import random
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "src" / "main" / "resources" / "seed"
RNG = random.Random(7)

POOL = {
    "java": [
        "int", "boolean", "double", "char", "String", "long", "float", "byte", "short",
        "void", "class", "interface", "public", "private", "protected", "static", "final",
        "new", "this", "super", "if", "else", "for", "while", "switch", "try", "catch",
        "throw", "throws", "import", "package", "extends", "implements", "enum", "record",
        "ArrayList", "HashMap", "HashSet", "LinkedList", "Optional", "Stream", "null",
        "true", "false", "main", "equals", "hashCode", "toString", "synchronized",
    ],
    "python": [
        "list", "dict", "tuple", "set", "str", "int", "float", "bool", "None", "True",
        "False", "def", "class", "if", "elif", "else", "for", "while", "import", "from",
        "try", "except", "finally", "raise", "with", "lambda", "yield", "pass", "break",
        "continue", "return", "len", "print", "input", "range", "open", "self", "__init__",
        "append", "pop", "split", "join", "json", "os", "sys", "asyncio", "NoneType",
    ],
    "cpp": [
        "int", "double", "float", "char", "bool", "void", "class", "struct", "public",
        "private", "protected", "namespace", "using", "new", "delete", "nullptr", "const",
        "static", "virtual", "override", "final", "template", "auto", "sizeof", "enum",
        "std::vector", "std::string", "std::map", "std::set", "std::cout", "std::cin",
        "include", "main", "try", "catch", "throw", "unique_ptr", "shared_ptr", "RAII",
    ],
}


def lang_key(path_name: str) -> str:
    if "python" in path_name:
        return "python"
    if "cpp" in path_name:
        return "cpp"
    return "java"


def letras_para_alts(item: dict) -> list[str]:
    return [
        item["alternativaA"],
        item["alternativaB"],
        item["alternativaC"],
        item["alternativaD"],
    ]


def alts_para_item(item: dict, alts: list[str], correta_texto: str) -> None:
    item["alternativaA"] = alts[0]
    item["alternativaB"] = alts[1]
    item["alternativaC"] = alts[2]
    item["alternativaD"] = alts[3]
    # Recalcula letra da correta pelo texto
    for i, letra in enumerate("ABCD"):
        if alts[i].strip() == correta_texto.strip():
            item["respostaCorreta"] = letra
            return
    # fallback por letra antiga se texto não bateu
    idx = "ABCD".index(item["respostaCorreta"].strip().upper())
    # garante que a correta esteja em alguma posição
    if correta_texto not in alts:
        alts[idx] = correta_texto
        item["alternativaA"] = alts[0]
        item["alternativaB"] = alts[1]
        item["alternativaC"] = alts[2]
        item["alternativaD"] = alts[3]
    item["respostaCorreta"] = "ABCD"[alts.index(correta_texto)]


def normaliza(s: str) -> str:
    return " ".join(s.strip().split()).lower()


def corrigir_item(item: dict, pool: list[str]) -> bool:
    alts = letras_para_alts(item)
    letra = item["respostaCorreta"].strip().upper()
    if letra not in "ABCD":
        letra = "A"
        item["respostaCorreta"] = "A"
    correta_texto = alts["ABCD".index(letra)]

    # Se houver duplicata (case-insensitive) ou alternativa vazia/genérica demais
    norms = [normaliza(a) for a in alts]
    genericas = {"tipo", "opção", "opcao", "errada", "incorreta", "inválida", "invalida", ""}
    precisa = len(set(norms)) < 4 or any(n in genericas for n in norms)

    if not precisa:
        return False

    usados = {normaliza(correta_texto)}
    novas = [None, None, None, None]
    idx_correta = "ABCD".index(letra)
    novas[idx_correta] = correta_texto.strip()

    # Mantém distractors úteis já existentes
    for i, alt in enumerate(alts):
        if i == idx_correta:
            continue
        n = normaliza(alt)
        if n and n not in usados and n not in genericas and len(alt.strip()) > 1:
            novas[i] = alt.strip()
            usados.add(n)

    candidatos = [c for c in pool if normaliza(c) not in usados]
    RNG.shuffle(candidatos)

    for i in range(4):
        if novas[i] is None:
            if not candidatos:
                # último recurso: gera rótulo único sem repetir
                k = 1
                while normaliza(f"alternativa {k}") in usados:
                    k += 1
                novas[i] = f"alternativa {k}"
                usados.add(normaliza(novas[i]))
            else:
                escolhida = candidatos.pop()
                novas[i] = escolhida
                usados.add(normaliza(escolhida))

    # Embaralha posições mantendo a correta rastreável
    correta = novas[idx_correta]
    distractors = [novas[i] for i in range(4) if i != idx_correta]
    RNG.shuffle(distractors)
    final = distractors + [correta]
    RNG.shuffle(final)
    alts_para_item(item, final, correta)
    return True


def main() -> None:
    total_fix = 0
    for path in sorted(SEED.glob("perguntas-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        pool = POOL[lang_key(path.name)]
        fixed = 0
        for item in data:
            if corrigir_item(item, pool):
                fixed += 1
        # validação final
        ainda = 0
        for item in data:
            alts = letras_para_alts(item)
            if len({normaliza(a) for a in alts}) < 4:
                ainda += 1
            letra = item["respostaCorreta"].strip().upper()
            if letra not in "ABCD":
                ainda += 1
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{path.name}: corrigidas={fixed}, ainda_invalidas={ainda}")
        total_fix += fixed

        # exemplo do caso da imagem
        for item in data:
            if "8 bits" in item["enunciado"].lower() or "inteiro de 8" in item["enunciado"].lower():
                print("  ex:", item["enunciado"])
                print("   ", [item["alternativaA"], item["alternativaB"], item["alternativaC"], item["alternativaD"]],
                      "->", item["respostaCorreta"])
    print("total corrigidas:", total_fix)


if __name__ == "__main__":
    main()
