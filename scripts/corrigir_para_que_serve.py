#!/usr/bin/env python3
"""Corrige enunciados vagos 'Para que serve X?' e alternativas do molde genérico."""

from __future__ import annotations

import json
import random
import re
import unicodedata
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "src" / "main" / "resources" / "seed"
RNG = random.Random(42)

PARA_QUE_RE = re.compile(r"^para que serve\b", re.I)

TYPE_LABEL_RE = re.compile(
    r"^(tipo\s+)?("
    r"primitivo|booleano|inteiro|texto|caractere|decimal|ponteiro|referência|referencia|"
    r"boolean|void|enum|interface|classe|struct|namespace|modificador"
    r")(\s|$)",
    re.I,
)

GENERIC_DISTRACTORS = {
    "tipo booleano", "tipo para texto", "tipo texto", "tipo inteiro",
    "tipo caractere", "tipo decimal", "modificador de acesso", "modificador",
    "inteiro", "booleano", "caractere", "texto", "void", "enum", "ponteiro",
    "ponteiro nulo", "referência", "namespace", "interface", "bool", "int",
}

ACTION_VERBS = (
    "declara", "define", "armazena", "representa", "retorna", "devolve",
    "permite", "cria", "remove", "compara", "atribui", "lança", "verifica",
    "acessa", "inclui", "importa", "indica", "adiciona", "insere", "itera",
    "extrai", "ordena", "converte", "gerencia", "protege", "encapsula",
    "sincroniza", "executa", "chama", "invoca", "inicializa", "herda",
    "implementa", "sobrescreve", "abre", "fecha", "lê", "le", "escreve",
    "imprime", "captura", "trata", "controla", "valida", "filtra", "mapeia",
    "laço", "condicional", "estrutura", "bloco", "método", "função", "funcao",
    "operador", "palavra-chave", "sem valor de retorno", "ponto flutuante",
    "curto-circuito", "negação", "incremento", "decremento", "acesso",
)


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def normalize(text: str) -> str:
    text = strip_accents(text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def is_type_label(alt: str) -> bool:
    n = normalize(alt)
    if n in GENERIC_DISTRACTORS or n.startswith("tipo "):
        return True
    return bool(TYPE_LABEL_RE.match(n))


def is_action_description(alt: str) -> bool:
    low = strip_accents(alt.lower())
    return any(v in low for v in ACTION_VERBS)


def needs_alt_fix(item: dict) -> bool:
    enunciado = item["enunciado"]
    if not PARA_QUE_RE.match(enunciado.strip()):
        return False
    alts = [item["alternativaA"], item["alternativaB"], item["alternativaC"], item["alternativaD"]]
    type_count = sum(1 for a in alts if is_type_label(a))
    action_count = sum(1 for a in alts if is_action_description(a))
    generic_hits = sum(1 for a in alts if normalize(a) in GENERIC_DISTRACTORS)
    if type_count >= 2 and action_count <= 1:
        return True
    if generic_hits >= 2:
        return True
    correta = alts["ABCD".index(item["respostaCorreta"].strip().upper())]
    if is_type_label(correta) and type_count >= 3:
        return True
    return False

# (correta, [errada1, errada2, errada3])
ALT_FIXES: dict[tuple[str, str], tuple[str, list[str]]] = {
    # --- Java tipos primitivos ---
    ("java", "int"): (
        "declarar variáveis que armazenam números inteiros",
        [
            "declarar variáveis que armazenam texto",
            "representar valores verdadeiro ou falso",
            "definir a visibilidade de atributos e métodos",
        ],
    ),
    ("java", "boolean"): (
        "armazenar valores verdadeiro ou falso",
        [
            "armazenar números inteiros",
            "armazenar um único caractere Unicode",
            "armazenar números decimais de ponto flutuante",
        ],
    ),
    ("java", "double"): (
        "armazenar números decimais de ponto flutuante de 64 bits",
        [
            "armazenar números inteiros",
            "armazenar texto",
            "representar valores verdadeiro ou falso",
        ],
    ),
    ("java", "float"): (
        "armazenar números decimais de ponto flutuante de 32 bits",
        [
            "armazenar números inteiros de 64 bits",
            "armazenar texto",
            "definir pacotes no código",
        ],
    ),
    ("java", "char"): (
        "armazenar um único caractere Unicode",
        [
            "armazenar sequências completas de texto",
            "armazenar números inteiros",
            "representar valores verdadeiro ou falso",
        ],
    ),
    ("java", "byte"): (
        "armazenar números inteiros de 8 bits",
        [
            "armazenar texto",
            "armazenar números de 64 bits",
            "representar valores verdadeiro ou falso",
        ],
    ),
    ("java", "short"): (
        "armazenar números inteiros de 16 bits",
        [
            "armazenar texto",
            "armazenar números de 64 bits",
            "armazenar números decimais",
        ],
    ),
    ("java", "long"): (
        "armazenar números inteiros de 64 bits",
        [
            "armazenar números de 8 bits",
            "armazenar um caractere",
            "representar valores verdadeiro ou falso",
        ],
    ),
    # --- C++ tipos fundamentais ---
    ("cpp", "int"): (
        "declarar variáveis que armazenam números inteiros",
        [
            "declarar variáveis que armazenam texto",
            "representar valores verdadeiro ou falso",
            "indicar ausência de valor de retorno",
        ],
    ),
    ("cpp", "double"): (
        "armazenar números de ponto flutuante de precisão dupla",
        [
            "armazenar números inteiros",
            "armazenar um único caractere",
            "representar valores verdadeiro ou falso",
        ],
    ),
    ("cpp", "float"): (
        "armazenar números de ponto flutuante de precisão simples",
        [
            "armazenar números inteiros de 64 bits",
            "declarar enumerações",
            "indicar ausência de retorno",
        ],
    ),
    ("cpp", "char"): (
        "armazenar um único caractere",
        [
            "armazenar sequências completas de texto automaticamente",
            "indicar ausência de retorno",
            "representar valores verdadeiro ou falso",
        ],
    ),
    ("cpp", "bool"): (
        "armazenar valores verdadeiro ou falso",
        [
            "armazenar números inteiros",
            "representar ponteiros nulos",
            "declarar referências a objetos",
        ],
    ),
    ("cpp", "void"): (
        "indicar ausência de valor de retorno ou tipo vazio",
        [
            "armazenar números inteiros",
            "declarar namespaces",
            "definir classes",
        ],
    ),
}

LANG_PRIMITIVES = {
    "java": {"int", "boolean", "double", "float", "char", "byte", "short", "long", "void"},
    "cpp": {"int", "double", "float", "char", "bool", "void"},
    "python": {"int", "float", "bool", "str", "None", "True", "False"},
}

LANG_MODIFIERS = {
    "java": {"public", "private", "protected", "static", "final", "abstract", "synchronized", "volatile", "transient", "native", "strictfp"},
    "cpp": {"public", "private", "protected", "const", "static", "virtual", "override", "final", "inline", "constexpr", "friend"},
    "python": {"global", "nonlocal"},
}

LANG_KEYWORDS = {
    "java": {
        "class", "interface", "enum", "record", "new", "this", "super", "package", "import",
        "extends", "implements", "try", "catch", "finally", "throw", "throws", "var", "instanceof", "default", "assert",
    },
    "cpp": {
        "class", "struct", "enum", "namespace", "using", "new", "delete", "typedef", "template", "typename",
        "try", "catch", "throw", "auto", "nullptr", "sizeof",
    },
    "python": {
        "def", "class", "return", "if", "elif", "else", "for", "while", "import", "from", "as", "pass",
        "break", "continue", "try", "except", "finally", "raise", "with", "lambda", "yield", "async", "await", "del", "assert",
    },
}

LANG_OPERATORS = {
    "java": {"==", "=", "!=", "&&", "||", "!", "%", "++", "--", "+=", ".", "?:", "<<", ">>", ">>>", "&", "|", "^"},
    "cpp": {"==", "=", "!=", "&&", "||", "!", "%", "++", "--", "+=", ".", "->", "::"},
    "python": {"and", "or", "not", "in", "is"},
}

LANG_BUILTINS = {
    "python": {"len", "print", "input", "range", "type", "sum", "max", "min", "open", "enumerate", "zip", "map", "filter", "sorted", "isinstance"},
}

LANG_CONTAINERS = {
    "cpp": {"std::vector", "std::string", "std::map", "std::set", "std::unordered_map", "std::unordered_set",
            "std::stack", "std::queue", "std::deque", "std::priority_queue", "std::pair", "std::tuple",
            "std::optional", "std::unique_ptr", "std::shared_ptr", "std::weak_ptr"},
}


def lang_key(name: str) -> str:
    if "python" in name:
        return "python"
    if "cpp" in name:
        return "cpp"
    return "java"


def get_alts(item: dict) -> list[str]:
    return [item["alternativaA"], item["alternativaB"], item["alternativaC"], item["alternativaD"]]


def set_alts(item: dict, alts: list[str], correta_idx: int) -> None:
    item["alternativaA"] = alts[0]
    item["alternativaB"] = alts[1]
    item["alternativaC"] = alts[2]
    item["alternativaD"] = alts[3]
    item["respostaCorreta"] = "ABCD"[correta_idx]


def extract_subject(enunciado: str) -> tuple[str, str] | None:
    """Retorna (tipo, token) para enunciados 'Para que serve ...'."""
    e = enunciado.strip()

    patterns = [
        (r"(?i)Para que serve o tipo primitivo\s+(\S+)\s*\??$", "token"),
        (r"(?i)Para que serve o modificador\s+(\S+)\s*\??$", "token"),
        (r"(?i)Para que serve a palavra-chave\s+(\S+)\s*\??$", "token"),
        (r"(?i)Para que serve o operador\s+(.+?)\s*\??$", "operador"),
        (r"(?i)Para que serve a função built-in\s+(\S+)\s*\??$", "token"),
        (r"(?i)Para que serve o método\s+(.+?)\s+em\s+(.+?)\s*\??$", "metodo"),
        (r"(?i)Para que serve o método\s+(.+?)\s*\??$", "metodo"),
        (r"(?i)Para que serve o container\s+(\S+)\s*\??$", "token"),
        (r"(?i)Para que serve o fluxo padrão\s+(\S+)\s*\??$", "token"),
        (r"(?i)Para que serve o recurso\s+(\S+)\s+da biblioteca padrão\s*\??$", "token"),
        (r"(?i)Para que serve a diretiva de pré-processador\s+(\S+)\s*\??$", "token"),
        (r"(?i)Para que serve\s+O\s+operador\s+['\"]?(.+?)['\"]?\s*\??$", "operador"),
        (r"(?i)Para que serve\s+['\"](.+?)['\"]\s+em\s+(.+?)\s*\??$", "metodo"),
        (r"(?i)Para que serve\s+['\"](.+?)['\"]\s*\??$", "token"),
        (r"(?i)Para que serve\s+(.+?)\s+na prática\s*\??$", "pratica"),
        (r"(?i)Para que serve\s+(.+?)\s*\??$", "geral"),
    ]

    for pattern, kind in patterns:
        m = re.match(pattern, e)
        if not m:
            continue
        if kind == "metodo" and len(m.groups()) == 2:
            return (kind, f"{m.group(1)} em {normalize_token(m.group(2))}")
        return (kind, normalize_token(m.group(1)))

    return None


def normalize_token(token: str) -> str:
    return token.strip().rstrip("?")


def already_formatted(enunciado: str) -> bool:
    return bool(
        re.match(
            r"(?i)^Para que serve (o tipo primitivo|o modificador|a palavra-chave|o operador|"
            r"a função built-in|o método|o container|o fluxo padrão|o recurso|a diretiva de pré-processador)\b",
            enunciado.strip(),
        )
    )


def rewrite_enunciado(enunciado: str, lang: str) -> str:
    e = " ".join(enunciado.split()).strip()
    e = re.sub(r"\?+$", "?", e)

    if already_formatted(e):
        return e

    parsed = extract_subject(e)
    if not parsed:
        return e

    kind, token = parsed
    token_base = normalize_token(token.split(" em ")[0])

    if kind == "operador":
        return f"Para que serve o operador {token}?"

    if kind == "metodo":
        method, _, ctx = token.partition(" em ")
        return f"Para que serve o método {method} em {ctx}?"

    if kind == "pratica":
        return f"Para que serve {token} na prática?"

    if token_base.startswith("#"):
        return f"Para que serve a diretiva de pré-processador {token_base}?"

    if token_base.startswith("std::"):
        if token_base in LANG_CONTAINERS.get(lang, set()):
            return f"Para que serve o container {token_base}?"
        if token_base in {"std::cout", "std::cin"}:
            return f"Para que serve o fluxo padrão {token_base}?"
        return f"Para que serve o recurso {token_base} da biblioteca padrão?"

    if token_base in LANG_PRIMITIVES.get(lang, set()):
        return f"Para que serve o tipo primitivo {token_base}?"

    if token_base in LANG_MODIFIERS.get(lang, set()):
        return f"Para que serve o modificador {token_base}?"

    if token_base in LANG_OPERATORS.get(lang, set()):
        return f"Para que serve o operador {token_base}?"

    if token_base in LANG_BUILTINS.get(lang, set()):
        return f"Para que serve a função built-in {token_base}?"

    if "." in token_base and lang == "python":
        return f"Para que serve o método {token_base}?"

    if token_base in LANG_KEYWORDS.get(lang, set()):
        return f"Para que serve a palavra-chave {token_base}?"

    if "()" in token_base or "(...)" in token_base:
        return f"Para que serve o método {token_base}?"

    return f"Para que serve {token_base}?"


def fix_alternatives(item: dict, lang: str, token: str) -> bool:
    key = (lang, token.lower())
    if key not in ALT_FIXES:
        return False

    correta, erradas = ALT_FIXES[key]
    alts = [correta, *erradas]
    RNG.shuffle(alts)
    set_alts(item, alts, alts.index(correta))
    return True


def process_item(item: dict, lang: str) -> tuple[bool, bool]:
    enun_changed = False
    alt_changed = False

    if not PARA_QUE_RE.match(item["enunciado"].strip()):
        return enun_changed, alt_changed

    parsed = extract_subject(item["enunciado"])
    token_key = ""
    if parsed:
        _, token = parsed
        token_key = normalize_token(token.split(" em ")[0]).lower()

    fix_alts = needs_alt_fix(item)

    novo_enun = rewrite_enunciado(item["enunciado"], lang)
    if novo_enun != item["enunciado"]:
        item["enunciado"] = novo_enun
        enun_changed = True

    if fix_alts and token_key:
        if fix_alternatives(item, lang, token_key):
            alt_changed = True

    return enun_changed, alt_changed


def main() -> None:
    total_enun = 0
    total_alt = 0

    for path in sorted(SEED.glob("perguntas-*.json")):
        lang = lang_key(path.name)
        data = json.loads(path.read_text(encoding="utf-8"))
        enun_n = alt_n = 0

        for item in data:
            e_changed, a_changed = process_item(item, lang)
            if e_changed:
                enun_n += 1
            if a_changed:
                alt_n += 1

        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{path.name}: enunciados={enun_n}, alternativas={alt_n}")
        total_enun += enun_n
        total_alt += alt_n

    print(f"total: enunciados={total_enun}, alternativas={total_alt}")


if __name__ == "__main__":
    main()
