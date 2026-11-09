#!/usr/bin/env python3
"""Audita perguntas do seed: duplicatas e molde genérico de alternativas nonsense."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "src" / "main" / "resources" / "seed"
OUT = Path(__file__).resolve().parent / "relatorios"

SIMILARITY_THRESHOLD = 0.88

# Alternativas recicladas típicas do molde genérico (rótulos de tipo/modificador).
GENERIC_DISTRACTORS = {
    "tipo booleano",
    "tipo para texto",
    "tipo texto",
    "tipo inteiro",
    "tipo inteiro 64 bits",
    "tipo inteiro de 8 bits",
    "tipo inteiro de 16 bits",
    "tipo inteiro de 64 bits",
    "tipo caractere",
    "tipo decimal",
    "tipo texto completo",
    "modificador de acesso",
    "modificador",
    "inteiro",
    "booleano",
    "caractere",
    "texto",
    "void",
    "enum",
    "ponteiro",
    "ponteiro nulo",
    "referência",
    "namespace",
    "interface",
    "classe",
    "macro",
    "template",
    "protected",
    "public",
    "private",
    "import",
    "record",
    "throws",
    "toString",
    "new",
    "this",
    "super",
    "main",
    "null",
    "true",
    "false",
    "string",
    "float",
    "double",
    "char",
    "byte",
    "short",
    "long",
    "bool",
    "int",
}

TYPE_LABEL_RE = re.compile(
    r"^(tipo\s+)?("
    r"primitivo|booleano|inteiro|texto|caractere|decimal|ponteiro|referência|referencia|"
    r"boolean|void|enum|interface|classe|struct|namespace|modificador"
    r")(\s|$)",
    re.I,
)

MODIFIER_LABEL_RE = re.compile(r"^modificador", re.I)

PURPOSE_QUESTION_RE = re.compile(
    r"para que serve|qual a fun[cç][aã]o|para que [eé] usad",
    re.I,
)

TOKEN_IN_QUOTES_RE = re.compile(r"['\"]([^'\"]+)['\"]")

BROKEN_ENUNCIADO_RE = re.compile(
    r"para que serve\s+O\s+operador|"
    r"^o que [eé] (devolve|declara|representa|permite|cria|remove|abre|lança|define)\b",
    re.I,
)

ACTION_VERBS = (
    "declara",
    "define",
    "armazena",
    "representa",
    "retorna",
    "devolve",
    "permite",
    "cria",
    "remove",
    "compara",
    "atribui",
    "lança",
    "lanca",
    "abre",
    "extrai",
    "adiciona",
    "insere",
    "remove",
    "itera",
    "captura",
    "trata",
    "verifica",
    "acessa",
    "inclui",
    "importa",
    "exporta",
    "herda",
    "implementa",
    "sobrescreve",
    "inicializa",
    "encapsula",
    "sincroniza",
    "serializa",
    "converte",
    "ordena",
    "filtra",
    "mapeia",
    "reduz",
    "agrupa",
    "executa",
    "chama",
    "invoca",
    "aloca",
    "libera",
    "gerencia",
    "protege",
    "estende",
    "lança exceção",
    "trata exceção",
    "soma e atribui",
    "resto da divisão",
    "negação lógica",
    "incremento",
    "decremento",
    "acesso a membro",
    "compara igualdade",
    "atribui um valor",
    "verifica diferença",
    "curto-circuito",
    "laço",
    "condicional",
    "estrutura",
    "bloco",
    "método",
    "função",
    "funcao",
    "operador",
    "palavra-chave",
    "sem valor de retorno",
    "ponto flutuante",
    "precisão",
    "caractere unicode",
    "verdadeiro/falso",
    "números inteiros",
    "numeros inteiros",
)


@dataclass
class Finding:
    arquivo: str
    indice: int
    dificuldade: int
    categoria: str
    motivo: str
    enunciado: str
    alternativas: list[str] = field(default_factory=list)
    resposta_correta: str = ""
    detalhes: dict = field(default_factory=dict)


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def normalize(text: str) -> str:
    text = strip_accents(text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def get_alternativas(item: dict) -> list[str]:
    return [
        item["alternativaA"],
        item["alternativaB"],
        item["alternativaC"],
        item["alternativaD"],
    ]


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def is_type_label(alt: str) -> bool:
    n = normalize(alt)
    if n in GENERIC_DISTRACTORS:
        return True
    if TYPE_LABEL_RE.match(n):
        return True
    if MODIFIER_LABEL_RE.match(n):
        return True
    if n.startswith("tipo "):
        return True
  # rótulos curtos de uma palavra que são tokens de linguagem
    if len(n.split()) == 1 and n in GENERIC_DISTRACTORS:
        return True
    return False


def is_action_description(alt: str) -> bool:
    low = strip_accents(alt.lower())
    return any(v in low for v in ACTION_VERBS)


def is_purpose_question(enunciado: str) -> bool:
    return bool(PURPOSE_QUESTION_RE.search(enunciado))


def count_type_labels(alts: list[str]) -> int:
    return sum(1 for a in alts if is_type_label(a))


def count_action_descriptions(alts: list[str]) -> int:
    return sum(1 for a in alts if is_action_description(a))


def detect_molde_generico(item: dict) -> list[str]:
    """Retorna lista de motivos se a pergunta parece usar molde nonsense."""
    motivos: list[str] = []
    enunciado = item["enunciado"]
    alts = get_alternativas(item)
    correta = alts["ABCD".index(item["respostaCorreta"].strip().upper())]

    type_count = count_type_labels(alts)
    action_count = count_action_descriptions(alts)
    generic_hits = [a for a in alts if normalize(a) in GENERIC_DISTRACTORS]

    if BROKEN_ENUNCIADO_RE.search(enunciado):
        motivos.append("enunciado_malformado")

    if is_purpose_question(enunciado):
        if type_count >= 2:
            motivos.append(f"molde_tipo_em_pergunta_de_proposito ({type_count}/4 alternativas sao rotulos de tipo)")

        if type_count >= 2 and action_count <= 1:
            motivos.append("alternativas_desconexas_sem_verbo_de_acao")

        if is_type_label(correta) and type_count >= 3:
            motivos.append("resposta_correta_e_rotulo_de_tipo_em_pergunta_de_proposito")

        # Pergunta sobre token primitivo/tipo com distractors genéricos
        m = TOKEN_IN_QUOTES_RE.search(enunciado)
        if m:
            token = m.group(1).lower()
            primitives = {
                "int", "boolean", "double", "float", "char", "byte", "short", "long",
                "void", "bool", "str", "none", "true", "false",
            }
            if token in primitives and type_count >= 2:
                motivos.append(f"tipo_primitivo_{token}_com_distractors_genericos")

    if len(generic_hits) >= 2:
        motivos.append(f"distractors_genericos_reciclados ({', '.join(generic_hits[:3])})")

    # Alternativas muito curtas e sem relação (1-2 palavras, sem verbo)
    short_non_action = [
        a for a in alts if len(a.split()) <= 2 and not is_action_description(a)
    ]
    if is_purpose_question(enunciado) and len(short_non_action) >= 3:
        motivos.append("alternativas_curtas_sem_descricao_de_uso")

    # Par pergunta-resposta invertida: "O que é [frase da resposta correta anterior]?"
    if re.match(r"^o que (é|representa)\s+", enunciado, re.I):
        subject = re.sub(r"^o que (é|representa)\s+", "", enunciado, flags=re.I)
        subject = subject.rstrip("?").strip()
        if is_action_description(subject) or len(subject.split()) >= 4:
            wrong = [a for i, a in enumerate(alts) if "ABCD"[i] != item["respostaCorreta"].strip().upper()]
            if count_type_labels(wrong) >= 2 or all(len(w.split()) <= 2 for w in wrong):
                motivos.append("par_invertido_enunciado_usa_texto_da_resposta")

    return list(dict.fromkeys(motivos))


def find_duplicates(data: list[dict], arquivo: str) -> list[Finding]:
    findings: list[Finding] = []
    by_norm: dict[str, list[int]] = defaultdict(list)

    for i, item in enumerate(data):
        by_norm[normalize(item["enunciado"])].append(i)

    for norm, indices in by_norm.items():
        if len(indices) > 1:
            for idx in indices:
                findings.append(
                    Finding(
                        arquivo=arquivo,
                        indice=idx,
                        dificuldade=data[idx]["dificuldade"],
                        categoria="duplicata_exata",
                        motivo=f"enunciado identico a indices {', '.join(str(i) for i in indices if i != idx)}",
                        enunciado=data[idx]["enunciado"],
                        alternativas=get_alternativas(data[idx]),
                        resposta_correta=data[idx]["respostaCorreta"],
                        detalhes={"grupo": indices},
                    )
                )

    n = len(data)
    for i in range(n):
        for j in range(i + 1, n):
            sim = similarity(data[i]["enunciado"], data[j]["enunciado"])
            if sim >= SIMILARITY_THRESHOLD and normalize(data[i]["enunciado"]) != normalize(data[j]["enunciado"]):
                for idx, other in ((i, j), (j, i)):
                    findings.append(
                        Finding(
                            arquivo=arquivo,
                            indice=idx,
                            dificuldade=data[idx]["dificuldade"],
                            categoria="duplicata_quase_exata",
                            motivo=f"similaridade {sim:.0%} com indice {other}",
                            enunciado=data[idx]["enunciado"],
                            alternativas=get_alternativas(data[idx]),
                            resposta_correta=data[idx]["respostaCorreta"],
                            detalhes={"par": [i, j], "similaridade": round(sim, 4)},
                        )
                    )
    return findings


def audit_file(path: Path) -> list[Finding]:
    data = json.loads(path.read_text(encoding="utf-8"))
    arquivo = path.name
    findings: list[Finding] = []

    findings.extend(find_duplicates(data, arquivo))

    for i, item in enumerate(data):
        motivos = detect_molde_generico(item)
        for motivo in motivos:
            findings.append(
                Finding(
                    arquivo=arquivo,
                    indice=i,
                    dificuldade=item["dificuldade"],
                    categoria="molde_generico",
                    motivo=motivo,
                    enunciado=item["enunciado"],
                    alternativas=get_alternativas(item),
                    resposta_correta=item["respostaCorreta"],
                )
            )

        # Alternativas duplicadas dentro da mesma pergunta
        norms = [normalize(a) for a in get_alternativas(item)]
        if len(set(norms)) < 4:
            findings.append(
                Finding(
                    arquivo=arquivo,
                    indice=i,
                    dificuldade=item["dificuldade"],
                    categoria="alternativas_duplicadas",
                    motivo="alternativas repetidas na mesma pergunta",
                    enunciado=item["enunciado"],
                    alternativas=get_alternativas(item),
                    resposta_correta=item["respostaCorreta"],
                )
            )

    return findings


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple] = set()
    out: list[Finding] = []
    for f in findings:
        key = (f.arquivo, f.indice, f.categoria, f.motivo)
        if key not in seen:
            seen.add(key)
            out.append(f)
    return sorted(out, key=lambda f: (f.arquivo, f.categoria, f.indice, f.motivo))


def write_csv(findings: list[Finding], path: Path) -> None:
    fields = [
        "arquivo",
        "indice",
        "dificuldade",
        "categoria",
        "motivo",
        "enunciado",
        "alternativaA",
        "alternativaB",
        "alternativaC",
        "alternativaD",
        "respostaCorreta",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for item in findings:
            row = {
                "arquivo": item.arquivo,
                "indice": item.indice,
                "dificuldade": item.dificuldade,
                "categoria": item.categoria,
                "motivo": item.motivo,
                "enunciado": item.enunciado,
                "alternativaA": item.alternativas[0] if item.alternativas else "",
                "alternativaB": item.alternativas[1] if len(item.alternativas) > 1 else "",
                "alternativaC": item.alternativas[2] if len(item.alternativas) > 2 else "",
                "alternativaD": item.alternativas[3] if len(item.alternativas) > 3 else "",
                "respostaCorreta": item.resposta_correta,
            }
            w.writerow(row)


def write_json(findings: list[Finding], path: Path, summary: dict) -> None:
    payload = {
        "resumo": summary,
        "achados": [asdict(f) for f in findings],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_molde_resumo(findings: list[Finding], path: Path) -> dict:
    """Um registro por pergunta com todos os motivos agregados."""
    by_key: dict[tuple[str, int], Finding] = {}
    motivos_map: dict[tuple[str, int], list[str]] = defaultdict(list)

    for f in findings:
        if f.categoria != "molde_generico":
            continue
        key = (f.arquivo, f.indice)
        motivos_map[key].append(f.motivo)
        if key not in by_key:
            by_key[key] = f

    rows: list[dict] = []
    for key in sorted(by_key, key=lambda k: (k[0], k[1])):
        f = by_key[key]
        rows.append(
            {
                "arquivo": f.arquivo,
                "indice": f.indice,
                "dificuldade": f.dificuldade,
                "motivos": " | ".join(dict.fromkeys(motivos_map[key])),
                "enunciado": f.enunciado,
                "alternativaA": f.alternativas[0],
                "alternativaB": f.alternativas[1],
                "alternativaC": f.alternativas[2],
                "alternativaD": f.alternativas[3],
                "respostaCorreta": f.resposta_correta,
            }
        )

    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    por_arquivo: dict[str, int] = defaultdict(int)
    for r in rows:
        por_arquivo[r["arquivo"]] += 1
    return {"total_perguntas_molde_generico": len(rows), "por_arquivo": dict(por_arquivo)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    all_findings: list[Finding] = []

    for path in sorted(SEED.glob("perguntas-*.json")):
        file_findings = audit_file(path)
        all_findings.extend(file_findings)

    all_findings = dedupe_findings(all_findings)

    by_file: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_cat: dict[str, int] = defaultdict(int)
    indices_por_arquivo: dict[str, set[int]] = defaultdict(set)

    for f in all_findings:
        by_file[f.arquivo][f.categoria] += 1
        by_cat[f.categoria] += 1
        indices_por_arquivo[f.arquivo].add(f.indice)

    summary = {
        "total_achados": len(all_findings),
        "por_categoria": dict(by_cat),
        "por_arquivo": {k: dict(v) for k, v in by_file.items()},
        "indices_unicos_por_arquivo": {k: sorted(v) for k, v in indices_por_arquivo.items()},
        "threshold_similaridade": SIMILARITY_THRESHOLD,
    }

    csv_path = OUT / "auditoria_perguntas.csv"
    json_path = OUT / "auditoria_perguntas.json"
    molde_csv_path = OUT / "auditoria_molde_generico.csv"
    write_csv(all_findings, csv_path)
    molde_resumo = write_molde_resumo(all_findings, molde_csv_path)
    summary["molde_generico_resumo"] = molde_resumo
    write_json(all_findings, json_path, summary)

    print("=== RESUMO DA AUDITORIA ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nRelatorios gerados:")
    print(f"  CSV completo     : {csv_path}")
    print(f"  CSV molde generico: {molde_csv_path}")
    print(f"  JSON             : {json_path}")

    print("\n=== EXEMPLOS MOLDE GENERICO (primeiros 15) ===")
    shown = 0
    for f in all_findings:
        if f.categoria != "molde_generico":
            continue
        print(f"\n[{f.arquivo}#{f.indice}] {f.enunciado}")
        print(f"  motivo: {f.motivo}")
        print(f"  A={f.alternativas[0]!r} B={f.alternativas[1]!r}")
        print(f"  C={f.alternativas[2]!r} D={f.alternativas[3]!r} (-> {f.resposta_correta})")
        shown += 1
        if shown >= 15:
            break


if __name__ == "__main__":
    main()
