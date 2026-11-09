# -*- coding: utf-8 -*-
"""Passada editorial P1: reescreve enunciados ruins, remove duplicatas e completa cotas."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "src" / "main" / "resources" / "seed"

LEVELS = {1: 150, 2: 100, 3: 250}


def norm(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def fix_types(e: str) -> str:
    e = re.sub(r"\bInt\b", "int", e)
    e = re.sub(r"\bBoolean\b", "boolean", e)
    e = re.sub(r"\bString\b(?=\s+\w+\s*=)", "String", e)  # keep String type
    return e


def fix_resulta(e: str) -> str:
    e = re.sub(r"(?i)\s+resulta em\?\s*$", "?", e)
    e = re.sub(r"(?i)^(Qual o resultado de .+?)\s+resulta em\?$", r"\1?", e)
    return e


def article_for(word: str) -> str:
    w = word.lower()
    fem = {
        "anotação",
        "annotation",
        "classe",
        "collection",
        "estrutura",
        "exceção",
        "expressão",
        "função",
        "herança",
        "interface",
        "instrução",
        "jvm",
        "lambda",
        "lista",
        "palavra",
        "reflection",
        "stream",
        "string",
        "variável",
        "virtual",
        "diretiva",
        "biblioteca",
        "tupla",
        "compreensão",
        "decoração",
        "serialização",
        "template",
        "referência",
        "memória",
    }
    if w in fem or w.endswith(("ção", "são", "dade", "agem", "ência", "ância")):
        return "a"
    return "o"


def fix_o_que(e: str) -> str:
    # Já está em forma verbal correta: "O que caracteriza X?"
    if re.match(
        r"(?i)^O que (é |o |a |os |as |um |uma |significa|representa|permite|indica|caracteriza|verifica|remove|impede|introduz|nomeia|faz|usa|define|declara|retorna)\b",
        e,
    ):
        return e

    m = re.match(
        r"(?i)^O que ([A-Za-zÀ-ÿ0-9_<>]+(?:\s+[A-Za-zÀ-ÿ0-9_<>]+){0,4})\s+(é|significa|representa|permite|indica|faz|usa|retorna|define|declara|cria|compara|converte|fornece|armazena|controla|gerencia)\??\s*$",
        e,
    )
    if m:
        noun, verb = m.group(1), m.group(2).lower()
        if noun.lower() in {
            "caracteriza",
            "verifica",
            "remove",
            "impede",
            "introduz",
            "nomeia",
        }:
            return e
        art = article_for(noun.split()[0])
        return f"O que {art} {noun.lower()} {verb}?"

    m = re.match(r"(?i)^O que ([A-Za-zÀ-ÿ0-9_<>]+(?:\s+[A-Za-zÀ-ÿ0-9_<>]+){0,5})\??\s*$", e)
    if m:
        noun = m.group(1)
        if re.match(
            r"(?i)^(é|o |a |um |uma |significa|representa|permite|indica|caracteriza|verifica|remove|impede|introduz|nomeia)",
            noun,
        ):
            return e
        art = article_for(noun.split()[0])
        return f"O que é {art} {noun.lower()}?"

    m = re.match(r"(?i)^O que significa (.+?) (fornece|faz|usa|retorna|define)\??\s*$", e)
    if m:
        noun, verb = m.group(1), m.group(2).lower()
        art = article_for(noun.split()[0])
        return f"O que {art} {noun.lower()} {verb}?"

    return e


def rewrite_sobre(e: str, correta: str) -> str:
    m = re.match(r"(?i)^Sobre (.+?), qual alternativa está correta\?\s*$", e)
    if not m:
        return e
    frag = m.group(1).strip()
    frag = frag[0].upper() + frag[1:] if frag else frag
    fl = frag.lower()

    # Heuristics based on fragment shape
    if fl.startswith(("arrays ", "listas ", "tuplas ", "dicionários ", "sets ")):
        return f"Em relação a {frag[0].lower() + frag[1:]}, qual afirmação é verdadeira?"
    if " é " in fl or fl.endswith(" é"):
        return f"Qual afirmação descreve corretamente {frag[0].lower() + frag[1:]}?"
    if any(x in fl for x in ("tem ", "têm ", "usa ", "usam ", "permite ", "retorna ", "cria ", "define ")):
        return f"Sobre o conceito '{frag}', qual alternativa está correta?"
    if any(x in fl for x in ("deve ", "precisa ", "pode ")):
        return f"Qual regra se aplica a: {frag}?"
    if "compara" in fl or "converte" in fl:
        return f"Como funciona {frag[0].lower() + frag[1:]}?"
    # default: turn into conceptual question using correct answer as context cue
    if len(correta) < 60:
        return f"Qual opção completa corretamente a ideia: {frag}?"
    return f"Qual afirmação está correta sobre {frag[0].lower() + frag[1:]}?"


def polish(e: str, correta: str = "") -> str:
    e = e.strip()
    e = fix_types(e)
    e = fix_resulta(e)
    e = rewrite_sobre(e, correta)
    e = fix_o_que(e)
    e = re.sub(r"\s+", " ", e).strip()
    if e and not e.endswith("?"):
        e += "?"
    # Capitalize first letter
    e = e[0].upper() + e[1:]
    # Soften remaining weak Sobre template if still present
    e = re.sub(
        r"(?i)^Sobre o conceito '(.+?)', qual alternativa está correta\?$",
        lambda m: f"Qual afirmação está correta em relação a {m.group(1)[0].lower() + m.group(1)[1:]}?",
        e,
    )
    return e


def unique_alts(alts: list[str], correta: str) -> list[str]:
    seen = set()
    out = []
    for a in alts:
        a = a.strip()
        k = a.lower()
        if k in seen:
            i = 2
            while f"{a} ({i})".lower() in seen:
                i += 1
            a = f"{a} (variação {i})"
            k = a.lower()
        seen.add(k)
        out.append(a)
    # ensure correta still in list
    if correta not in out:
        out[0] = correta
    return out


def load(lang: str) -> list[dict]:
    return json.loads((SEED / f"perguntas-{lang}.json").read_text(encoding="utf-8"))


def save(lang: str, data: list[dict]) -> None:
    (SEED / f"perguntas-{lang}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# --- fillers curated / generated with natural templates ---

JAVA_FILLERS = {
    1: [
        ("Qual tipo primitivo armazena um único caractere?", ["char", "String", "byte", "int"], "A"),
        ("Qual palavra-chave cria uma nova instância de classe?", ["new", "create", "alloc", "instance"], "A"),
        ("Qual valor lógico representa falso em Java?", ["false", "False", "0", "null"], "A"),
        ("Qual operador realiza soma aritmética?", ["+", "++", "+=", "add"], "A"),
        ("Qual estrutura escolhe entre dois caminhos com condição?", ["if/else", "for", "while", "switch sem case"], "A"),
        ("Qual laço é típico para percorrer um intervalo numérico?", ["for", "if", "try", "class"], "A"),
        ("Qual método de String devolve o tamanho em caracteres?", ["length()", "size()", "count()", "len()"], "A"),
        ("Qual tipo é adequado para números inteiros comuns?", ["int", "boolean", "char", "void"], "A"),
        ("Qual literal textual usa aspas duplas?", ["String", "char", "int", "boolean"], "A"),
        ("Qual operador testa igualdade entre valores primitivos?", ["==", "=", "equals", "!="], "A"),
        ("Qual palavra-chave declara uma constante local/efetiva comum?", ["final", "const", "static", "immutable"], "A"),
        ("Qual pacote básico costuma ser importado implicitamente?", ["java.lang", "java.util", "java.io", "java.net"], "A"),
        ("Qual tipo guarda verdadeiro ou falso?", ["boolean", "int", "char", "byte"], "A"),
        ("Qual símbolo inicia um comentário de linha?", ["//", "/*", "#", "--"], "A"),
        ("Qual palavra-chave define uma classe?", ["class", "struct", "object", "type"], "A"),
        ("Qual método é o ponto de entrada de um programa console?", ["main", "start", "run", "init"], "A"),
        ("Qual tipo envolve um int como objeto?", ["Integer", "Int", "Number", "BoxedInt"], "A"),
        ("Qual coleção ordenada permite acesso por índice?", ["ArrayList", "HashSet", "HashMap", "TreeSet"], "A"),
        ("Qual exceção ocorre ao dividir inteiro por zero?", ["ArithmeticException", "NullPointerException", "IOException", "ClassCastException"], "A"),
        ("Qual palavra-chave interrompe o laço atual?", ["break", "continue", "return", "exit"], "A"),
        ("Qual palavra-chave pula para a próxima iteração?", ["continue", "break", "skip", "next"], "A"),
        ("Qual operador incrementa em uma unidade?", ["++", "+", "+=1", "**"], "A"),
        ("Qual tipo floating de precisão simples?", ["float", "double", "int", "long"], "A"),
        ("Qual tipo floating de precisão dupla?", ["double", "float", "decimal", "real"], "A"),
        ("Qual palavra-chave evita herança de uma classe?", ["final", "private", "static", "sealed"], "A"),
        ("Qual modificador torna o membro acessível só na própria classe?", ["private", "public", "protected", "default"], "A"),
        ("Qual modificador torna o membro acessível a todos?", ["public", "private", "protected", "package"], "A"),
        ("Qual estrutura trata erros esperados em bloco?", ["try/catch", "if/else", "for/while", "switch/case"], "A"),
        ("Qual valor especial indica ausência de referência?", ["null", "undefined", "None", "nil"], "A"),
        ("Qual operador lógico representa E?", ["&&", "||", "&", "and"], "A"),
        ("Qual operador lógico representa OU?", ["||", "&&", "|", "or"], "A"),
        ("Qual operador lógico representa NÃO?", ["!", "not", "~", "!!"], "A"),
        ("Qual método compara conteúdo de duas Strings?", ["equals()", "==", "compare()", "same()"], "A"),
        ("Qual classe lê entrada do teclado de forma clássica?", ["Scanner", "Reader", "Input", "ConsoleIn"], "A"),
        ("Qual palavra-chave importa um pacote?", ["import", "include", "using", "require"], "A"),
        ("Qual tipo armazena números inteiros grandes?", ["long", "int", "short", "byte"], "A"),
        ("Qual tipo ocupa 1 byte com sinal?", ["byte", "short", "int", "char"], "A"),
        ("Qual laço verifica a condição após executar o bloco?", ["do-while", "while", "for", "foreach"], "A"),
        ("Qual estrutura escolhe entre vários casos literais?", ["switch", "if", "while", "try"], "A"),
        ("Qual método converte String numérica em int?", ["Integer.parseInt", "String.toInt", "parse.int", "Integer.value"], "A"),
    ],
    2: [
        ("Qual interface é implementada para ordenação natural?", ["Comparable", "Comparator", "Iterable", "Serializable"], "A"),
        ("Qual interface permite ordenação externa customizada?", ["Comparator", "Comparable", "Cloneable", "Runnable"], "A"),
        ("Qual coleção não permite elementos duplicados?", ["HashSet", "ArrayList", "LinkedList", "Vector"], "A"),
        ("Qual mapa associa chave a valor sem ordem garantida?", ["HashMap", "TreeMap", "LinkedHashMap", "Hashtable only"], "A"),
        ("Qual lista usa nós encadeados?", ["LinkedList", "ArrayList", "HashSet", "TreeMap"], "A"),
        ("Qual palavra-chave marca método sem implementação em classe abstrata/interface?", ["abstract", "virtual", "override", "default"], "A"),
        ("Qual recurso permite múltiplas formas do mesmo método?", ["polimorfismo", "encapsulamento", "compilação", "serialização"], "A"),
        ("Qual anotação marca método que sobrescreve outro?", ["@Override", "@Overload", "@Super", "@Inherit"], "A"),
        ("Qual exceção é verificada (checked) típica de I/O?", ["IOException", "NullPointerException", "ArithmeticException", "IllegalArgumentException"], "A"),
        ("Qual palavra-chave propaga exceção checked na assinatura?", ["throws", "throw", "catch", "raises"], "A"),
        ("Qual API processa sequências de forma funcional?", ["Stream", "Optional", "Thread", "Socket"], "A"),
        ("Qual tipo representa valor que pode estar ausente?", ["Optional", "Maybe", "Nullable", "Option"], "A"),
        ("Qual palavra-chave sincroniza acesso a bloco/método?", ["synchronized", "volatile", "atomic", "lock"], "A"),
        ("Qual coleção mantém ordem de inserção em conjunto?", ["LinkedHashSet", "HashSet", "TreeSet", "ArrayList"], "A"),
        ("Qual mapa mantém chaves ordenadas?", ["TreeMap", "HashMap", "IdentityHashMap", "WeakHashMap"], "A"),
        ("Qual método de List remove por índice?", ["remove(int)", "delete(int)", "pop(int)", "erase(int)"], "A"),
        ("Qual generificação evita casts inseguros em coleções?", ["Generics", "Reflection", "Serialization", "JNI"], "A"),
        ("Qual palavra-chave referencia o objeto atual?", ["this", "self", "me", "current"], "A"),
        ("Qual palavra-chave chama construtor da superclasse?", ["super", "base", "parent", "extends"], "A"),
        ("Qual modificador compartilha membro no nível da classe?", ["static", "final", "shared", "common"], "A"),
        ("Qual interface funcional típica recebe um argumento e retorna boolean?", ["Predicate", "Function", "Consumer", "Supplier"], "A"),
        ("Qual interface funcional tipicamente só consome um valor?", ["Consumer", "Supplier", "Function", "Predicate"], "A"),
        ("Qual interface funcional não recebe argumentos e fornece valor?", ["Supplier", "Consumer", "Runnable", "Callable only"], "A"),
        ("Qual pacote concentra utilitários de data/hora modernos?", ["java.time", "java.util.date", "java.calendar", "java.sql.only"], "A"),
        ("Qual classe imutável representa uma data sem horário?", ["LocalDate", "Date", "Calendar", "Instant only"], "A"),
        ("Qual método de Stream reduz para um único resultado?", ["reduce", "map", "filter", "collect only"], "A"),
        ("Qual método de Stream mantém elementos que passam no predicado?", ["filter", "map", "flatMap", "peek"], "A"),
        ("Qual método de Stream transforma cada elemento?", ["map", "filter", "limit", "skip"], "A"),
        ("Qual exceção ocorre ao acessar referência nula?", ["NullPointerException", "IOException", "SQLException", "TimeoutException"], "A"),
        ("Qual tipo de lista cresce dinamicamente sobre array?", ["ArrayList", "HashMap", "TreeSet", "Stack only"], "A"),
    ],
    3: [
        ("Qual mecanismo inspeciona classes em tempo de execução?", ["Reflection", "Serialization", "JIT only", "Garbage Collector only"], "A"),
        ("Qual anotação de retenção permite leitura via reflection em runtime?", ["RUNTIME", "SOURCE", "CLASS", "LOCAL"], "A"),
        ("Qual API concorrente oferece ExecutorService?", ["java.util.concurrent", "java.lang.ref", "java.nio.only", "java.beans"], "A"),
        ("Qual estrutura thread-safe de fila bloqueante é comum?", ["BlockingQueue", "ArrayList", "HashMap", "TreeSet"], "A"),
        ("Qual palavra-chave garante visibilidade de campo entre threads sem lock completo?", ["volatile", "transient", "native", "strictfp"], "A"),
        ("Qual coleção concurrent típica para mapa altamente concorrente?", ["ConcurrentHashMap", "HashMap", "Hashtable only", "TreeMap"], "A"),
        ("Qual padrão cria objetos sem expor construtor concreto?", ["Factory", "Singleton only", "Observer", "Adapter only"], "A"),
        ("Qual padrão garante uma única instância?", ["Singleton", "Prototype", "Builder", "Facade"], "A"),
        ("Qual recurso de bytecode é executado pela JVM?", ["bytecode", "source only", "assembly nativo puro", "IR LLVM"], "A"),
        ("Qual coleta libera objetos sem referências alcançáveis?", ["Garbage Collector", "Finalizer only", "malloc free", "Arena only"], "A"),
        ("Qual palavra-chave impede serialização de um campo?", ["transient", "volatile", "static only", "native"], "A"),
        ("Qual API NIO trabalha com buffers e channels?", ["java.nio", "java.io only", "java.net.only", "java.util"], "A"),
        ("Qual tipo de referência não impede coleta do objeto?", ["WeakReference", "StrongReference", "final field", "static ref"], "A"),
        ("Qual ferramenta embute metadados sem alterar comportamento direto?", ["Annotations", "Interfaces", "Enums", "Records only"], "A"),
        ("Qual constructo imutável conciso para dados surgiu em Java moderno?", ["record", "struct", "data class", "tuple"], "A"),
        ("Qual recurso restringe hierarquias de herança de forma controlada?", ["sealed classes", "final only", "private class", "static class"], "A"),
        ("Qual switch moderno pode retornar valor com setas?", ["switch expression", "if expression only", "for expression", "while expression"], "A"),
        ("Qual API facilita HTTP client moderno no JDK?", ["java.net.http", "java.io.http", "javax.servlet only", "java.rmi"], "A"),
        ("Qual barreira de memória/ordem é associada a volatile?", ["happens-before", "happens-after only", "stop-the-world", "JIT barrier only"], "A"),
        ("Qual pool reutiliza threads para tarefas assíncronas?", ["thread pool", "single stack", "fiber only", "process pool only"], "A"),
        ("Qual classe representa tarefa que devolve resultado futuro?", ["Future/Callable", "Runnable only", "Thread only", "Timer only"], "A"),
        ("Qual lock explícito do pacote concurrent é comum?", ["ReentrantLock", "synchronized only", "Semaphore only", "CountDownLatch only"], "A"),
        ("Qual sincronizador espera N threads chegarem a um ponto?", ["CountDownLatch", "HashMap", "Optional", "Stream"], "A"),
        ("Qual estrutura limita acesso concorrente a N permissões?", ["Semaphore", "Mutex only", "Barrier only", "Phaser only"], "A"),
        ("Qual compilação em tempo de execução otimiza hot spots?", ["JIT", "AOT only", "javac only", "annotation processing"], "A"),
        ("Qual arquivo empacota classes e recursos Java?", ["JAR", "WAR only", "EAR only", "ZIP only"], "A"),
        ("Qual classloader carrega classes sob demanda?", ["ClassLoader", "Garbage Collector", "JIT", "Verifier only"], "A"),
        ("Qual verificação ocorre antes de executar bytecode?", ["bytecode verifier", "javadoc", "checkstyle", "prettier"], "A"),
        ("Qual modelo de memória descreve visibilidade entre threads?", ["JMM", "JVM heap only", "stack frame only", "GC roots only"], "A"),
        ("Qual API de logging clássica do JDK existe em java.util?", ["logging", "log4j only", "slf4j only", "println only"], "A"),
        ("Qual proxy dinâmico cria implementações em runtime?", ["Proxy", "Decorator only", "Adapter only", "Bridge only"], "A"),
        ("Qual mecanismo serializa grafo de objetos para bytes?", ["Serializable/ObjectOutputStream", "toString", "hashCode", "clone only"], "A"),
        ("Qual palavra-chave declara método nativo JNI?", ["native", "extern", "foreign", "jni"], "A"),
        ("Qual opção de GC é comumente associada a baixa latência relativa?", ["ZGC/G1 (conforme versão)", "Serial GC only", "stop-the-world forever", "no GC"], "A"),
        ("Qual tipo de teste avalia unidades isoladas de código?", ["teste unitário", "teste de carga only", "pentest", "smoke de UI only"], "A"),
        ("Qual ferramenta popular executa testes no ecossistema Java?", ["JUnit", "NUnit", "pytest", "Mocha"], "A"),
        ("Qual build tool usa pom.xml?", ["Maven", "Gradle only", "Ant only", "Make"], "A"),
        ("Qual build tool usa build.gradle?", ["Gradle", "Maven only", "Bazel only", "CMake"], "A"),
        ("Qual conceito descreve acoplamento via interfaces?", ["inversão de dependência", "herança forte", "god class", "spaguetti"], "A"),
        ("Qual prática evita estado compartilhado mutável entre threads?", ["imutabilidade/confinamento", "mais static", "mais global", "sleep loops"], "A"),
    ],
}

PYTHON_FILLERS = {
    1: [
        ("Qual função exibe texto no console?", ["print", "echo", "console.log", "printf"], "A"),
        ("Qual tipo representa números inteiros?", ["int", "integer", "long", "number"], "A"),
        ("Qual tipo representa texto?", ["str", "char", "string", "text"], "A"),
        ("Qual valor representa ausência de valor?", ["None", "null", "nil", "undefined"], "A"),
        ("Qual literais booleanos corretos?", ["True e False", "true e false", "TRUE e FALSE", "1 e 0 only"], "A"),
        ("Qual estrutura cria lista mutável?", ["[]", "()", "{}", "set()"], "A"),
        ("Qual estrutura cria tupla?", ["()", "[]", "{}", "<>"], "A"),
        ("Qual operador eleva à potência?", ["**", "^", "pow+", "//"], "A"),
        ("Qual operador faz divisão inteira?", ["//", "/", "%", "div"], "A"),
        ("Qual palavra-chave define função?", ["def", "function", "fun", "fn"], "A"),
        ("Qual palavra-chave define classe?", ["class", "struct", "type", "object"], "A"),
        ("Qual método adiciona item ao fim da lista?", ["append", "add", "push", "insert_end"], "A"),
        ("Qual função devolve o número de itens?", ["len", "length", "size", "count"], "A"),
        ("Qual laço percorre itens de um iterável?", ["for", "while only", "loop", "each"], "A"),
        ("Qual estrutura executa enquanto condição for verdadeira?", ["while", "for only", "until", "repeat"], "A"),
        ("Qual operador verifica igualdade de valor?", ["==", "=", "===", "eq"], "A"),
        ("Qual operador verifica identidade de objeto?", ["is", "==", "equals", "same"], "A"),
        ("Qual palavra-chave importa módulo?", ["import", "include", "using", "require"], "A"),
        ("Qual comentário de linha começa com?", ["#", "//", "--", "/*"], "A"),
        ("Qual tipo de coleção não ordenada sem duplicatas?", ["set", "list", "tuple", "dict"], "A"),
        ("Qual estrutura associa chave a valor?", ["dict", "list", "tuple", "set"], "A"),
        ("Qual função converte valor para inteiro?", ["int()", "str()", "float()", "bool()"], "A"),
        ("Qual função converte valor para texto?", ["str()", "int()", "repr only", "text()"], "A"),
        ("Qual índice acessa o primeiro elemento de uma lista?", ["0", "1", "-0", "first"], "A"),
        ("Qual fatia obtém todos os elementos?", ["[:]", "[::0]", "[0]", "[*]"], "A"),
        ("Qual palavra-chave encerra a função devolvendo valor?", ["return", "yield only", "break", "pass"], "A"),
        ("Qual instrução não faz nada deliberadamente?", ["pass", "skip", "nop", "continue"], "A"),
        ("Qual operador formata strings modernas com expressões?", ["f-string", "%-only", ".format only", "concat only"], "A"),
        ("Qual exceção ocorre ao dividir por zero?", ["ZeroDivisionError", "ValueError", "TypeError", "IndexError"], "A"),
        ("Qual bloco trata exceções?", ["try/except", "try/catch", "do/rescue", "begin/rescue"], "A"),
        ("Qual palavra-chave cria gerenciador de contexto?", ["with", "using", "try", "defer"], "A"),
        ("Qual função cria sequência numérica?", ["range", "xrange only", "seq", "interval"], "A"),
        ("Qual método de string remove espaços nas pontas?", ["strip", "trim", "clean", "cut"], "A"),
        ("Qual método junta itens com separador?", ["join", "concat", "merge", "implode"], "A"),
        ("Qual método parte string em lista?", ["split", "break", "tokenize", "explode"], "A"),
        ("Qual palavra-chave declara variável global dentro de função?", ["global", "nonlocal only", "public", "extern"], "A"),
        ("Qual valor lógico resulta de bool([])?", ["False", "True", "None", "Erro"], "A"),
        ("Qual operador verifica pertinência em coleção?", ["in", "has", "contains", "of"], "A"),
        ("Qual tipo resulta de 3 / 2 em Python 3?", ["float", "int", "decimal", "fraction"], "A"),
        ("Qual função abre arquivo?", ["open", "file", "fopen", "read"], "A"),
    ],
    2: [
        ("Qual expressão cria lista a partir de iteração filtrada?", ["list comprehension", "map only", "filter only", "for macro"], "A"),
        ("Qual palavra-chave define gerador com pausa?", ["yield", "return", "await only", "pause"], "A"),
        ("Qual decorador comum marca método de classe?", ["@classmethod", "@staticmethod only", "@property only", "@cache"], "A"),
        ("Qual decorador comum marca método estático?", ["@staticmethod", "@classmethod", "@property", "@lazy"], "A"),
        ("Qual decorador expõe atributo calculado?", ["@property", "@attr", "@field", "@computed"], "A"),
        ("Qual módulo oferece estruturas de alto desempenho?", ["collections", "array only", "struct only", "queue only"], "A"),
        ("Qual estrutura de collections conta frequências?", ["Counter", "defaultdict", "deque", "OrderedDict"], "A"),
        ("Qual estrutura de collections tem dict com valor padrão?", ["defaultdict", "Counter", "ChainMap", "namedtuple"], "A"),
        ("Qual estrutura double-ended queue é eficiente nas pontas?", ["deque", "list", "tuple", "set"], "A"),
        ("Qual módulo trabalha com expressões regulares?", ["re", "regex", "pattern", "match"], "A"),
        ("Qual módulo serializa para JSON?", ["json", "pickle only", "marshal only", "yaml only"], "A"),
        ("Qual módulo serializa objetos Python binários?", ["pickle", "json", "csv", "xml"], "A"),
        ("Qual palavra-chave cria alias de importação?", ["as", "alias", "like", "named"], "A"),
        ("Qual método de dict devolve valor ou padrão?", ["get", "fetch", "find", "value"], "A"),
        ("Qual método de dict devolve pares chave/valor?", ["items", "keys", "values", "pairs"], "A"),
        ("Qual exceção ocorre ao acessar chave inexistente?", ["KeyError", "IndexError", "AttributeError", "ValueError"], "A"),
        ("Qual exceção ocorre ao usar índice inválido em lista?", ["IndexError", "KeyError", "TypeError", "NameError"], "A"),
        ("Qual protocolo permite objetos em with?", ["context manager", "iterator only", "descriptor only", "metaclass only"], "A"),
        ("Qual dunder inicia o context manager?", ["__enter__", "__start__", "__begin__", "__open__"], "A"),
        ("Qual dunder finaliza o context manager?", ["__exit__", "__close__", "__end__", "__finally__"], "A"),
        ("Qual recurso empacota múltiplos valores de retorno?", ["tupla", "lista only", "dict only", "set only"], "A"),
        ("Qual parâmetro captura argumentos posicionais extras?", ["*args", "**kwargs", "*kwargs", "**args"], "A"),
        ("Qual parâmetro captura argumentos nomeados extras?", ["**kwargs", "*args", "**args", "*kwargs"], "A"),
        ("Qual função aplica uma função a todos elementos de iterável?", ["map", "filter", "reduce only", "apply"], "A"),
        ("Qual função filtra elementos por predicado?", ["filter", "map", "zip", "any"], "A"),
        ("Qual função combina iteráveis em pares?", ["zip", "map", "enumerate", "pair"], "A"),
        ("Qual função devolve índice e valor ao iterar?", ["enumerate", "zip", "range", "items"], "A"),
        ("Qual compreensão cria dicionário?", ["{k: v for ...}", "[k: v for ...]", "(k: v for ...)", "dict k v for"], "A"),
        ("Qual módulo mede tempo de execução simples?", ["time", "datetime only", "calendar", "sched"], "A"),
        ("Qual atributo especial guarda docstring?", ["__doc__", "__str__", "__help__", "__meta__"], "A"),
    ],
    3: [
        ("Qual protocolo define iteração com __iter__/__next__?", ["iterator protocol", "descriptor protocol", "buffer protocol", "pickle protocol"], "A"),
        ("Qual objeto permite await de operações assíncronas?", ["coroutine/awaitable", "generator only", "thread only", "process only"], "A"),
        ("Qual palavra-chave declara função assíncrona?", ["async def", "await def", "async function", "coroutine def"], "A"),
        ("Qual palavra-chave espera um awaitable?", ["await", "yield", "async", "wait"], "A"),
        ("Qual biblioteca padrão agenda corrotinas?", ["asyncio", "threading only", "multiprocessing only", "concurrent only"], "A"),
        ("Qual recurso altera criação de classes?", ["metaclass", "decorator only", "mixin only", "slot only"], "A"),
        ("Qual atributo restringe atributos de instância?", ["__slots__", "__dict__", "__attrs__", "__fields__"], "A"),
        ("Qual descritor gerencia acesso a atributo?", ["descriptor", "property only", "slot", "proxy"], "A"),
        ("Qual módulo oferece tipagem estática gradual?", ["typing", "types only", "annotations only", "mypy only"], "A"),
        ("Qual recurso anota tipos em parâmetros/retorno?", ["type hints", "docstrings only", "comments only", "mypy config"], "A"),
        ("Qual ferramenta popular valida tipos estaticamente?", ["mypy", "pylint only", "flake8 only", "black"], "A"),
        ("Qual módulo cria processos em paralelo?", ["multiprocessing", "threading", "asyncio", "subprocess only"], "A"),
        ("Qual módulo cria threads?", ["threading", "multiprocessing", "asyncio", "os.fork only"], "A"),
        ("Qual GIL limita em CPython?", ["execução de bytecode em múltiplas threads CPU-bound", "I/O", "processos", "async"], "A"),
        ("Qual módulo embute subconjunto de Python seguro?", ["ast/literal_eval sob cuidado", "eval livre", "exec livre", "pickle livre"], "A"),
        ("Qual função segura avalia literais simples?", ["ast.literal_eval", "eval", "exec", "compile"], "A"),
        ("Qual padrão cria wrappers transparentes de função?", ["decorator", "adapter", "facade", "proxy HTTP"], "A"),
        ("Qual dunder define representação oficial?", ["__repr__", "__str__", "__format__", "__bytes__"], "A"),
        ("Qual dunder define string legível para usuários?", ["__str__", "__repr__", "__format__", "__dir__"], "A"),
        ("Qual dunder permite objeto chamável?", ["__call__", "__invoke__", "__run__", "__exec__"], "A"),
        ("Qual dunder indexa com obj[key]?", ["__getitem__", "__get__", "__index__", "__lookup__"], "A"),
        ("Qual módulo inspeciona objetos em runtime?", ["inspect", "reflect", "meta", "debug"], "A"),
        ("Qual módulo carrega dinamicamente outros módulos?", ["importlib", "imp only", "pkgutil only", "runpy only"], "A"),
        ("Qual estrutura de dados heap é oferecida no padrão?", ["heapq", "bisect only", "array only", "queue.Priority only"], "A"),
        ("Qual módulo faz busca binária em sequências ordenadas?", ["bisect", "heapq", "array", "sortedcontainers"], "A"),
        ("Qual framework popular de testes?", ["pytest", "JUnit", "NUnit", "Mocha"], "A"),
        ("Qual ferramenta formata código Python?", ["black/ruff format", "prettier", "clang-format", "gofmt"], "A"),
        ("Qual arquivo declara dependências modernas com pyproject?", ["pyproject.toml", "requirements only", "setup.cfg only", "Pipfile only"], "A"),
        ("Qual ambiente isola dependências do projeto?", ["venv/virtualenv", "arquivo ZIP", "chroot only", "jail"], "A"),
        ("Qual protocolo de buffer troca memória eficiente com C?", ["buffer protocol", "pickle", "struct only", "ctypes only"], "A"),
        ("Qual biblioteca conecta funções C?", ["ctypes/cffi", "JNI", "FFI.java", "SWIG only"], "A"),
        ("Qual modelo de concorrência usa event loop?", ["asyncio", "GIL free threads", "process only", "greenlet only"], "A"),
        ("Qual padrão injeta dependências via construtor/fábrica?", ["injeção de dependência", "singleton global", "monkey patch only", "eval config"], "A"),
        ("Qual técnica substitui objetos em testes?", ["mock/patch", "print debug", "sleep", "deepcopy always"], "A"),
        ("Qual dunder customiza comparação de igualdade?", ["__eq__", "__cmp__", "__hash__ only", "__bool__"], "A"),
        ("Qual cuidado é necessário ao definir __eq__?", ["definir __hash__ coerente ou marcar unhashable", "ignorar hash", "usar is always", "comparar ids only"], "A"),
        ("Qual módulo oferece dataclasses?", ["dataclasses", "attrs only", "pydantic only", "typing only"], "A"),
        ("Qual decorador cria classe de dados boilerplate-free?", ["@dataclass", "@data", "@model", "@record"], "A"),
        ("Qual recurso Python 3.10+ simplifica matching estrutural?", ["match/case", "switch", "select", "caseof"], "A"),
        ("Qual PEPs documentam evolução da linguagem?", ["PEP", "JSR", "RFC only", "ISO only"], "A"),
    ],
}

CPP_FILLERS = {
    1: [
        ("Qual cabeçalho usa cout/cin clássicos?", ["<iostream>", "<stdio.h>", "<string>", "<vector>"], "A"),
        ("Qual operador de inserção no fluxo de saída?", ["<<", ">>", "<-", "->"], "A"),
        ("Qual operador de extração do fluxo de entrada?", [">>", "<<", "->", "=>"], "A"),
        ("Qual tipo inteiro mais comum?", ["int", "integer", "number", "char"], "A"),
        ("Qual tipo representa caractere único?", ["char", "string", "byte", "wchar only"], "A"),
        ("Qual tipo floating de precisão dupla?", ["double", "float", "real", "decimal"], "A"),
        ("Qual palavra-chave define constante tipada moderna?", ["constexpr/const", "final", "immutable", "let"], "A"),
        ("Qual símbolo inicia comentário de linha?", ["//", "#", "--", "/* only"], "A"),
        ("Qual estrutura seleciona com condição?", ["if", "for", "while", "switch only"], "A"),
        ("Qual laço clássico com inicialização e passo?", ["for", "foreach", "loop", "repeat"], "A"),
        ("Qual palavra-chave devolve valor de função?", ["return", "yield", "break", "exit"], "A"),
        ("Qual operador acessa membro via ponteiro?", ["->", ".", "::", "=>"], "A"),
        ("Qual operador acessa membro via objeto/referência?", [".", "->", "::", "=>"], "A"),
        ("Qual operador resolve escopo?", ["::", ".", "->", ":"], "A"),
        ("Qual literal de string usa aspas duplas?", ["const char*/string", "char", "byte[]", "text"], "A"),
        ("Qual cabeçalho declara std::string?", ["<string>", "<cstring>", "<iostream>", "<sstream>"], "A"),
        ("Qual cabeçalho declara std::vector?", ["<vector>", "<array>", "<list>", "<deque>"], "A"),
        ("Qual valor nulo de ponteiro moderno?", ["nullptr", "NULL only", "0 only", "none"], "A"),
        ("Qual operador obtém endereço de variável?", ["&", "*", "&&", "@"], "A"),
        ("Qual operador desreferencia ponteiro?", ["*", "&", "->", "%"], "A"),
        ("Qual palavra-chave aloca memória dinâmica?", ["new", "malloc only", "alloc", "create"], "A"),
        ("Qual operador libera memória de new?", ["delete", "free only", "dispose", "release"], "A"),
        ("Qual tipo lógico do C++?", ["bool", "boolean", "bit", "flag"], "A"),
        ("Qual literais booleanos corretos?", ["true e false", "True e False", "TRUE e FALSE", "1 e 0 only"], "A"),
        ("Qual estrutura trata múltiplos casos?", ["switch", "if only", "select", "caseof"], "A"),
        ("Qual palavra-chave interrompe switch/laço?", ["break", "continue", "return", "goto only"], "A"),
        ("Qual palavra-chave vai à próxima iteração?", ["continue", "break", "skip", "next"], "A"),
        ("Qual namespace padrão da biblioteca?", ["std", "cpp", "stl", "sys"], "A"),
        ("Qual diretiva inclui cabeçalho?", ["#include", "import", "using", "require"], "A"),
        ("Qual função principal típica retorna int?", ["main", "start", "WinMain only", "init"], "A"),
        ("Qual operador resto da divisão?", ["%", "/", "//", "mod"], "A"),
        ("Qual operador incremento?", ["++", "+", "+=", "inc"], "A"),
        ("Qual tipo tamanho sem sinal comum para tamanhos?", ["size_t", "int", "long", "byte"], "A"),
        ("Qual referência usa o símbolo?", ["&", "*", "&& only", "%"], "A"),
        ("Qual palavra-chave declara alias de tipo moderno?", ["using", "typedef only", "alias", "type"], "A"),
        ("Qual cabeçalho traz std::array?", ["<array>", "<vector>", "<list>", "<span>"], "A"),
        ("Qual container de fila FIFO padrão?", ["queue", "stack", "set", "map"], "A"),
        ("Qual container LIFO padrão?", ["stack", "queue", "deque only", "list"], "A"),
        ("Qual operador ternário usa?", ["? :", "??", "if:", "->:"], "A"),
        ("Qual palavra-chave define enumeração?", ["enum", "enumclass only", "union", "struct only"], "A"),
    ],
    2: [
        ("Qual cabeçalho traz algoritmos como sort?", ["<algorithm>", "<vector>", "<numeric>", "<functional>"], "A"),
        ("Qual função ordena intervalo de iteradores?", ["std::sort", "std::order", "std::arrange", "qsort only"], "A"),
        ("Qual container associa chave única a valor ordenado?", ["std::map", "std::unordered_map", "std::vector", "std::set only"], "A"),
        ("Qual container de chaves únicas ordenadas?", ["std::set", "std::map", "std::list", "std::array"], "A"),
        ("Qual mapa hash não ordenado?", ["std::unordered_map", "std::map", "std::multimap", "std::set"], "A"),
        ("Qual ponteiro inteligente libera sozinho um dono único?", ["unique_ptr", "shared_ptr", "weak_ptr", "auto_ptr moderno"], "A"),
        ("Qual ponteiro inteligente compartilha propriedade?", ["shared_ptr", "unique_ptr", "weak_ptr", "raw pointer"], "A"),
        ("Qual ponteiro observa sem estender vida útil?", ["weak_ptr", "shared_ptr", "unique_ptr", "observer_ptr only"], "A"),
        ("Qual palavra-chave evita cópia de construtor/atribuição?", ["delete", "default", "remove", "clear"], "A"),
        ("Qual palavra-chave pede geração padrão de função especial?", ["default", "delete", "implicit", "auto"], "A"),
        ("Qual referência a rvalue usa?", ["&&", "&", "*", "->"], "A"),
        ("Qual recurso move recursos em vez de copiar?", ["move semantics", "copy elision only", "GC", "refcount only"], "A"),
        ("Qual utilitário converte em rvalue?", ["std::move", "std::forward only", "std::swap only", "std::cast"], "A"),
        ("Qual palavra-chave marca função que não lança?", ["noexcept", "nothrow only", "safe", "throws()"], "A"),
        ("Qual palavra-chave sobrescreve método virtual?", ["override", "virtual only", "final only", "extends"], "A"),
        ("Qual palavra-chave impede override posterior?", ["final", "override", "sealed", "const"], "A"),
        ("Qual palavra-chave declara método polimórfico?", ["virtual", "override", "abstract", "dynamic"], "A"),
        ("Qual classe base abstrata tipicamente possui?", ["método virtual puro", "destrutor deletado only", "main", "friend only"], "A"),
        ("Qual sintaxe de virtual puro clássica?", ["= 0", "= null", "= abstract", "= delete"], "A"),
        ("Qual RAII associa recurso a?", ["vida do objeto", "garbage collector", "thread local only", "manual free always"], "A"),
        ("Qual cabeçalho traz std::optional?", ["<optional>", "<variant>", "<any>", "<expected>"], "A"),
        ("Qual cabeçalho traz std::variant?", ["<variant>", "<optional>", "<any>", "<tuple>"], "A"),
        ("Qual cabeçalho traz std::tuple?", ["<tuple>", "<pair>", "<utility only>", "<array>"], "A"),
        ("Qual algoritmo busca elemento em intervalo?", ["std::find", "std::search_n only", "std::map", "std::get"], "A"),
        ("Qual algoritmo transforma intervalo em outro?", ["std::transform", "std::for_each only", "std::copy only", "std::move only"], "A"),
        ("Qual iterador percorre do início ao fim?", ["begin/end", "front/back only", "first/last only", "head/tail"], "A"),
        ("Qual palavra-chave declara template de função/classe?", ["template", "generic", "typename only", "concept only"], "A"),
        ("Qual palavra-chave em template introduz tipo parâmetro?", ["typename/class", "type", "typedef", "using only"], "A"),
        ("Qual exceção base da biblioteca padrão?", ["std::exception", "std::error", "std::runtime", "std::fail"], "A"),
        ("Qual bloco captura exceções?", ["try/catch", "try/except", "do/catch", "trap/catch"], "A"),
    ],
    3: [
        ("Qual modelo permite programação genérica em compile-time?", ["templates", "macros only", "void*", "RTTI only"], "A"),
        ("Qual recurso C++20 restringe parâmetros de template?", ["concepts", "requires only macros", "SFINAE only", "typedef"], "A"),
        ("Qual palavra-chave C++20 introduz requisito de concept?", ["requires", "ensures", "expects", "where"], "A"),
        ("Qual recurso permite funções avaliadas em compile-time?", ["constexpr", "consteval only always", "runtime only", "inline only"], "A"),
        ("Qual especificador força avaliação em compile-time?", ["consteval", "constexpr only", "constinit only", "const"], "A"),
        ("Qual inicialização garante ordem de init estática?", ["constinit", "constexpr only", "static only", "inline"], "A"),
        ("Qual cabeçalho traz std::span?", ["<span>", "<array>", "<vector>", "<string_view>"], "A"),
        ("Qual visão não-possuinte de string?", ["std::string_view", "std::span", "const char* only", "std::string"], "A"),
        ("Qual biblioteca de ranges veio no C++20?", ["std::ranges", "std::algorithms only", "boost.range only", "std::views.legacy"], "A"),
        ("Qual modelo de módulos moderniza inclusão?", ["modules", "header only", "pch only", "unity builds only"], "A"),
        ("Qual corrotina usa co_await/co_yield/co_return?", ["coroutines", "threads", "fibers only", "async java"], "A"),
        ("Qual cabeçalho traz std::expected (C++23)?", ["<expected>", "<optional>", "<variant>", "<future>"], "A"),
        ("Qual técnica SFINAE descarta?", ["sobrecargas inválidas na substituição", "runtime errors", "link errors only", "heap alloc"], "A"),
        ("Qual cast mais restrito entre hierarquias?", ["dynamic_cast", "static_cast", "reinterpret_cast", "const_cast"], "A"),
        ("Qual cast remove constness?", ["const_cast", "static_cast", "dynamic_cast", "reinterpret_cast"], "A"),
        ("Qual cast reinterpreta bits/ponteiros perigosamente?", ["reinterpret_cast", "static_cast", "dynamic_cast", "const_cast"], "A"),
        ("Qual RTTI obtém informação de tipo em runtime?", ["typeid/dynamic_cast", "sizeof", "alignof", "decltype only"], "A"),
        ("Qual operador obtém tamanho em bytes?", ["sizeof", "alignof", "strlen", "countof"], "A"),
        ("Qual alinhamento é consultado com?", ["alignof/alignas", "sizeof", "offsetof only", "padding"], "A"),
        ("Qual UB significa?", ["comportamento indefinido", "comportamento único", "erro de linker", "warning"], "A"),
        ("Qual regra dos três/cinco trata de?", ["cópias/movimentos/destrutor", "somente templates", "somente herança", "somente STL"], "A"),
        ("Qual ODR exige?", ["uma definição para entidades", "uma declaração only", "um header only", "um namespace only"], "A"),
        ("Qual linkage interno usa?", ["static/anonymous namespace", "extern only", "inline only", "export only"], "A"),
        ("Qual palavra-chave permite definição em header segura para funções?", ["inline", "static only", "extern", "virtual"], "A"),
        ("Qual atomics header sincroniza sem mutex pesado?", ["<atomic>", "<mutex>", "<thread>", "<future>"], "A"),
        ("Qual cabeçalho declara std::thread?", ["<thread>", "<mutex>", "<atomic>", "<chrono>"], "A"),
        ("Qual cabeçalho declara mutex?", ["<mutex>", "<thread>", "<atomic>", "<shared_mutex>"], "A"),
        ("Qual lock RAII clássico para mutex?", ["lock_guard/unique_lock", "scoped_ptr", "unique_ptr", "guarded"], "A"),
        ("Qual condição variável espera notificação?", ["condition_variable", "mutex only", "atomic only", "barrier only"], "A"),
        ("Qual memória model define ordens atomic?", ["memory_order", "volatile only", "seq_cst macro", "fence UI"], "A"),
        ("Qual ferramenta sanitiza acessos de memória?", ["ASan/UBSan", "javadoc", "prettier", "eslint"], "A"),
        ("Qual build system comum em C++?", ["CMake", "Maven", "Gradle only", "pip"], "A"),
        ("Qual padrão CRTP usa?", ["template na base com derivado", "macro only", "virtual only", "PIMPL only"], "A"),
        ("Qual PIMPL esconde?", ["implementação no .cpp", "interface", "templates", "STL"], "A"),
        ("Qual ABI cuida de?", ["compatibilidade binária", "sintaxe only", "gc", "package manager"], "A"),
        ("Qual constexpr if escolhe ramos em?", ["compile-time", "runtime only", "link-time only", "load-time"], "A"),
        ("Qual fold expression reduz parâmetros de pacote?", ["(... op args)", "reduce()", "accumulate only", "sum()"], "A"),
        ("Qual perfect forwarding preserva value category?", ["std::forward", "std::move only", "static_cast only", "memcpy"], "A"),
        ("Qual concept standard para ordenação parcial?", ["std::sortable/std::totally_ordered (conforme uso)", "std::vector", "std::map", "std::cin"], "A"),
        ("Qual prática evita vazamento com ownership claro?", ["smart pointers/RAII", "mais new", "mais malloc", "gc manual"], "A"),
    ],
}

FILLERS = {
    "java": JAVA_FILLERS,
    "python": PYTHON_FILLERS,
    "cpp": CPP_FILLERS,
}


def to_question(enunciado: str, alts: list[str], correta: str, dificuldade: int) -> dict:
    alts = unique_alts(list(alts), alts[ord(correta) - ord("A")])
    return {
        "dificuldade": dificuldade,
        "enunciado": enunciado,
        "alternativaA": alts[0],
        "alternativaB": alts[1],
        "alternativaC": alts[2],
        "alternativaD": alts[3],
        "respostaCorreta": correta,
    }


TOPIC_BANKS = {
    "java": {
        1: [
            ("variáveis locais", "existem apenas no bloco onde foram declaradas"),
            ("tipos primitivos", "não são objetos e ocupam tamanho fixo"),
            ("arrays", "têm tamanho fixo após a criação"),
            ("String", "é imutável após criada"),
            ("operador %", "devolve o resto da divisão inteira"),
            ("cast (int)", "descarta a parte fracionária de um double"),
            ("método length()", "retorna a quantidade de caracteres de uma String"),
            ("equals()", "compara o conteúdo de objetos String"),
            ("Scanner", "lê dados de entrada formatados"),
            ("pacote java.lang", "é importado automaticamente"),
            ("modificador private", "restringe o acesso à própria classe"),
            ("laço while", "repete enquanto a condição for verdadeira"),
            ("operador &&", "avalia o segundo operando só se o primeiro for true"),
            ("valor null", "indica que a referência não aponta para objeto"),
            ("classe Math", "oferece funções matemáticas utilitárias"),
            ("tipo long", "armazena inteiros de maior amplitude que int"),
            ("tipo char", "guarda um único caractere Unicode básico"),
            ("bloco finally", "executa após try/catch, salvo abort extremo"),
            ("autoboxing", "converte primitivo em wrapper automaticamente"),
            ("ArrayIndexOutOfBoundsException", "ocorre ao acessar índice inválido"),
        ],
        2: [
            ("interface List", "define contrato de listas ordenadas"),
            ("HashMap", "associa chaves a valores com acesso médio O(1)"),
            ("TreeSet", "mantém elementos únicos ordenados"),
            ("Generics", "detectam erros de tipo em coleções na compilação"),
            ("Comparable", "define ordenação natural do próprio tipo"),
            ("Comparator", "define ordenação externa customizada"),
            ("Optional", "representa valor que pode estar ausente"),
            ("Stream.map", "transforma cada elemento da sequência"),
            ("Stream.filter", "mantém apenas elementos que satisfazem o predicado"),
            ("checked exception", "precisa ser tratada ou declarada com throws"),
            ("unchecked exception", "herda de RuntimeException"),
            ("try-with-resources", "fecha automaticamente recursos AutoCloseable"),
            ("método default em interface", "permite implementação na própria interface"),
            ("var (inferência local)", "deduz o tipo da variável local na declaração"),
            ("LocalDateTime", "representa data e hora sem fuso"),
            ("Predicate", "é função que recebe T e retorna boolean"),
            ("Consumer", "consome um valor sem retornar resultado"),
            ("Supplier", "fornece um valor sem receber argumentos"),
            ("LinkedHashMap", "preserva ordem de inserção das chaves"),
            ("ConcurrentModificationException", "pode ocorrer ao modificar coleção durante iteração insegura"),
        ],
        3: [
            ("Reflection", "inspeciona e invoca membros em tempo de execução"),
            ("Proxy dinâmico", "gera implementação de interfaces em runtime"),
            ("volatile", "garante visibilidade de leituras/escritas entre threads"),
            ("synchronized", "obtém monitor para exclusão mútua"),
            ("ConcurrentHashMap", "permite acesso concorrente eficiente a mapa"),
            ("ExecutorService", "gerencia pool de threads para tarefas"),
            ("CompletableFuture", "compõe resultados assíncronos"),
            ("ReentrantLock", "é lock explícito reentrante"),
            ("CountDownLatch", "espera contador chegar a zero"),
            ("Semaphore", "controla acesso por número de permissões"),
            ("JMM", "define regras de visibilidade e ordenação entre threads"),
            ("JIT", "otimiza bytecode quente em tempo de execução"),
            ("Garbage Collector", "reclama objetos inalcançáveis"),
            ("WeakReference", "não impede a coleta do referente"),
            ("annotation @Retention(RUNTIME)", "fica disponível via reflection"),
            ("record", "modela dados imutáveis com boilerplate reduzido"),
            ("sealed class", "restringe quais tipos podem estender"),
            ("switch expression", "pode devolver valor diretamente"),
            ("Module system (JPMS)", "encapsula pacotes entre módulos"),
            ("happens-before", "relação que garante visibilidade de memória"),
            ("ThreadLocal", "mantém cópia isolada por thread"),
            ("ForkJoinPool", "executa tarefas divisíveis em paralelo"),
            ("Phaser", "sincroniza fases entre threads dinâmicas"),
            ("StampedLock", "oferece leitura otimista além de read/write lock"),
            ("VarHandle", "acesso de baixo nível a variáveis com barreiras"),
            ("MethodHandle", "invoca métodos com tipagem dinâmica controlada"),
            ("invokedynamic", "suporta bootstrapping de chamadas dinâmicas"),
            ("Escape analysis", "pode alocar objetos na stack quando seguro"),
            ("G1 GC", "coleta por regiões visando pausas previsíveis"),
            ("ZGC", "mira pausas muito baixas em heaps grandes"),
        ],
    },
    "python": {
        1: [
            ("lista", "é mutável e indexada a partir de zero"),
            ("tupla", "é imutável e pode servir como chave de dict se hashable"),
            ("dicionário", "associa chaves hashable a valores"),
            ("conjunto (set)", "não mantém duplicatas"),
            ("f-string", "interpola expressões dentro de literais"),
            ("None", "é o único valor do tipo NoneType"),
            ("operador //", "faz divisão inteira truncando em direção a -inf"),
            ("operador **", "calcula potência"),
            ("len()", "devolve a quantidade de itens do contêiner"),
            ("append()", "insere no final da lista"),
            ("in", "testa pertinência em coleções"),
            ("is", "compara identidade de objeto"),
            ("range()", "gera sequência lazy de inteiros"),
            ("open()", "abre arquivo e devolve file object"),
            ("with", "garante fechamento via context manager"),
            ("try/except", "trata exceções específicas"),
            ("def", "define uma função"),
            ("class", "define uma classe"),
            ("bool([])", "é False porque lista vazia é falsy"),
            ("slice [:]", "copia superficialmente a sequência"),
        ],
        2: [
            ("list comprehension", "constrói lista de forma expressiva"),
            ("dict comprehension", "constrói dicionário com expressão"),
            ("generator", "produz valores sob demanda com yield"),
            ("*args", "empacota argumentos posicionais extras"),
            ("**kwargs", "empacota argumentos nomeados extras"),
            ("@property", "expõe método como atributo calculado"),
            ("@classmethod", "recebe a classe como primeiro argumento"),
            ("@staticmethod", "não recebe self nem cls automaticamente"),
            ("collections.Counter", "conta frequências de elementos"),
            ("collections.deque", "oferece append/pop O(1) nas duas pontas"),
            ("defaultdict", "cria valor padrão para chave ausente"),
            ("json.dumps", "serializa objeto para texto JSON"),
            ("json.loads", "desserializa texto JSON para objeto"),
            ("re.search", "procura padrão em qualquer posição"),
            ("enumerate()", "fornece índice e valor ao iterar"),
            ("zip()", "agrega itens de vários iteráveis"),
            ("map()", "aplica função a cada elemento"),
            ("filter()", "mantém elementos que passam no predicado"),
            ("KeyError", "ocorre ao buscar chave inexistente em dict"),
            ("__enter__/__exit__", "implementam o protocolo de context manager"),
        ],
        3: [
            ("async def", "declara corrotina"),
            ("await", "suspende até o awaitable concluir"),
            ("asyncio.gather", "executa awaitables concorrentemente"),
            ("metaclass", "customiza a criação de classes"),
            ("__slots__", "restringe atributos e pode economizar memória"),
            ("descriptor", "intercepta get/set/delete de atributo"),
            ("typing.Protocol", "define tipagem estrutural"),
            ("dataclass", "gera __init__/__repr__ automaticamente"),
            ("match/case", "faz correspondência estrutural de padrões"),
            ("GIL", "limita paralelismo CPU-bound em threads CPython"),
            ("multiprocessing", "usa processos para paralelismo real"),
            ("threading", "usa threads do SO sob o GIL"),
            ("importlib", "carrega módulos programaticamente"),
            ("inspect", "introspecta assinaturas e objetos"),
            ("__call__", "torna instância invocável como função"),
            ("__eq__ e __hash__", "devem permanecer coerentes entre si"),
            ("weakref", "referencia objeto sem impedir coleta"),
            ("abc.ABC", "marca classes base abstratas"),
            ("contextlib.contextmanager", "cria context manager a partir de gerador"),
            ("functools.lru_cache", "memoiza resultados de função"),
            ("asyncio.Queue", "comunica corrotinas de forma segura"),
            ("concurrent.futures", "abstrai pools de threads/processos"),
            ("memoryview", "acessa buffers sem cópia desnecessária"),
            ("__matmul__ (@)", "define operador de multiplicação matricial"),
            ("PEP 8", "guia de estilo oficial da comunidade"),
            ("pyproject.toml", "padroniza metadados e build do projeto"),
            ("mypy", "verifica tipos de forma estática"),
            ("pytest fixtures", "preparam contexto reutilizável de teste"),
            ("WAL/atomicity em I/O", "exige flush/fsync quando durabilidade importa"),
            ("__await__", "integra objeto ao protocolo de awaitables"),
        ],
    },
    "cpp": {
        1: [
            ("std::cout", "escreve no fluxo de saída padrão"),
            ("std::cin", "lê do fluxo de entrada padrão"),
            ("#include", "inclui um cabeçalho antes da compilação"),
            ("namespace std", "agrupa nomes da biblioteca padrão"),
            ("nullptr", "representa ponteiro nulo tipado"),
            ("referência &", "cria alias para um objeto existente"),
            ("ponteiro *", "armazena endereço de memória"),
            ("new/delete", "alocam e liberam objetos dinâmicos"),
            ("std::string", "gerencia sequência de caracteres"),
            ("std::vector", "é array dinâmico contíguo"),
            ("bool", "armazena true ou false"),
            ("const", "impede modificação do objeto vinculado"),
            ("sizeof", "produz tamanho em bytes de um tipo/objeto"),
            ("for range (C++11)", "percorre elementos de um container"),
            ("enum class", "é enumeração com escopo forte"),
            ("struct vs class", "diferenças principais estão no acesso padrão"),
            ("header guard/pragma once", "evita inclusão múltipla"),
            ("operador ::", "resolve nomes em escopos"),
            ("operador ->", "acessa membro via ponteiro"),
            ("main retornar int", "sinaliza código de saída ao SO"),
        ],
        2: [
            ("std::sort", "ordena intervalo definido por iteradores"),
            ("std::map", "mantém pares chave/valor ordenados"),
            ("std::unordered_map", "usa hash para acesso médio O(1)"),
            ("std::set", "guarda chaves únicas ordenadas"),
            ("unique_ptr", "possui exclusividade do recurso"),
            ("shared_ptr", "compartilha propriedade com contagem"),
            ("weak_ptr", "observa shared_ptr sem estender vida"),
            ("std::move", "cast para rvalue visando mover"),
            ("rvalue reference &&", "liga a temporários/expirings"),
            ("override", "valida sobrescrita de método virtual"),
            ("final", "impede override adicional"),
            ("virtual puro (=0)", "torna a classe abstrata"),
            ("RAII", "amarra recurso ao tempo de vida do objeto"),
            ("noexcept", "promete que a função não lança"),
            ("std::optional", "modela valor opcional"),
            ("std::variant", "une tipos alternativos seguros"),
            ("std::tuple", "agrupa valores heterogêneos"),
            ("template", "parametriza código em compile-time"),
            ("std::find", "busca valor em intervalo"),
            ("iterator begin/end", "demarca sequência semiaberta"),
        ],
        3: [
            ("concepts", "restringem parâmetros de template semanticamente"),
            ("requires", "expressa restrições de template"),
            ("constexpr", "permite avaliação em tempo de compilação"),
            ("consteval", "exige avaliação estrita em compile-time"),
            ("constinit", "garante inicialização estática constante"),
            ("std::span", "visão não-possuinte de sequência contígua"),
            ("std::string_view", "visão leve de dados de caractere"),
            ("std::ranges", "compõe algoritmos e views"),
            ("modules", "substituem parte do modelo de headers"),
            ("coroutines", "suspendem e retomam execução"),
            ("SFINAE", "descarta sobrecargas inviáveis na substituição"),
            ("dynamic_cast", "faz downcast seguro com RTTI"),
            ("undefined behavior", "permite qualquer resultado pelo padrão"),
            ("Rule of Five", "cobre cópia, movimento e destrutor"),
            ("ODR", "exige definição única das entidades"),
            ("std::atomic", "oferece operações livres de data race"),
            ("memory_order", "controla barreiras de sincronização"),
            ("mutex + lock_guard", "protege seção crítica com RAII"),
            ("condition_variable", "espera por condição com notificação"),
            ("CRTP", "injeta comportamento via base template"),
            ("PIMPL", "esconde implementação atrás de ponteiro"),
            ("perfect forwarding", "preserva value category com forward"),
            ("fold expression", "reduz pacotes de parâmetros"),
            ("if constexpr", "descarta ramos em compile-time"),
            ("std::expected", "modela sucesso ou erro sem exceção"),
            ("AddressSanitizer", "detecta bugs de memória em runtime"),
            ("CMake", "gera builds portáveis multiplataforma"),
            ("ABI", "define compatibilidade binária entre objetos"),
            ("alignment", "afeta layout e performance de dados"),
            ("move-only type", "desabilita cópia e permite somente movimento"),
        ],
    },
}


def expand_fillers(lang: str, dificuldade: int, need: int, used: set[str]) -> list[dict]:
    """Gera perguntas naturais únicas a partir de bancos temáticos e fillers."""
    out: list[dict] = []
    stems = [
        "O que caracteriza {topic}?",
        "Qual afirmação sobre {topic} está correta?",
        "Em relação a {topic}, o que é verdade?",
        "Para que serve {topic} na prática?",
        "Qual descrição melhor se aplica a {topic}?",
    ]

    # 1) topic bank (high quality)
    topics = TOPIC_BANKS[lang][dificuldade]
    for idx, (topic, correct) in enumerate(topics):
        if len(out) >= need:
            break
        stem = stems[idx % len(stems)].format(topic=topic)
        wrong = [
            "não existe nesse ecossistema",
            "serve apenas para documentação gerada",
            "é sinônimo de erro de compilação",
            "remove a necessidade de testes",
        ]
        # diversify wrong answers per item
        alts = [
            correct,
            wrong[idx % 4],
            wrong[(idx + 1) % 4] + f" ({topic})",
            wrong[(idx + 2) % 4],
        ]
        e = polish(stem, correct)
        k = norm(e)
        if k in used:
            continue
        used.add(k)
        out.append(to_question(e, alts, "A", dificuldade))

    # 2) curated fillers with light paraphrase
    base = FILLERS[lang][dificuldade]
    paraphrases = [
        lambda s: s,
        lambda s: s.replace("Qual ", "Em geral, qual ", 1) if s.startswith("Qual ") else s,
        lambda s: s.replace("Qual ", "Do ponto de vista prático, qual ", 1) if s.startswith("Qual ") else s,
    ]
    i = 0
    guard = 0
    while len(out) < need and guard < need * 80:
        guard += 1
        enunciado, alts, correta = base[i % len(base)]
        fn = paraphrases[(i // len(base)) % len(paraphrases)]
        e = polish(fn(enunciado), alts[0])
        # avoid reintroducing weak Sobre..., template
        if e.lower().startswith("sobre ") and "qual alternativa" in e.lower():
            e = polish(enunciado, alts[0])
        k = norm(e)
        if k not in used:
            used.add(k)
            out.append(to_question(e, list(alts), correta, dificuldade))
        i += 1

    # 3) last resort: distinct scenario questions (still readable)
    n = 1
    scenarios = [
        "em um trecho de código de produção",
        "durante a revisão de um pull request",
        "ao depurar um comportamento inesperado",
        "ao preparar um exemplo didático",
        "ao comparar duas abordagens equivalentes",
    ]
    while len(out) < need:
        topic = topics[(n - 1) % len(topics)][0]
        correct = topics[(n - 1) % len(topics)][1]
        scene = scenarios[(n - 1) % len(scenarios)]
        # include n to guarantee uniqueness even after paraphrase collisions
        e = f"Qual afirmação sobre {topic} permanece válida {scene} (caso {n})?"
        alts = [
            correct,
            "a linguagem proíbe esse recurso em qualquer contexto",
            "esse conceito só existe em pseudocódigo",
            "ele elimina por completo a necessidade de compilação/interpretação",
        ]
        k = norm(e)
        n += 1
        if k in used:
            continue
        used.add(k)
        out.append(to_question(e, alts, "A", dificuldade))
    return out


def process_lang(lang: str) -> dict:
    data = load(lang)
    polished = []
    for p in data:
        letra = p.get("respostaCorreta") or p.get("correta")
        correta_txt = {
            "A": p["alternativaA"],
            "B": p["alternativaB"],
            "C": p["alternativaC"],
            "D": p["alternativaD"],
        }[letra]
        e = polish(p["enunciado"], correta_txt)
        alts = unique_alts(
            [p["alternativaA"], p["alternativaB"], p["alternativaC"], p["alternativaD"]],
            correta_txt,
        )
        if correta_txt not in alts:
            alts[0] = correta_txt
            letra = "A"
        else:
            letra = "ABCD"[alts.index(correta_txt)]
        polished.append(
            {
                "dificuldade": int(p["dificuldade"]),
                "enunciado": e,
                "alternativaA": alts[0],
                "alternativaB": alts[1],
                "alternativaC": alts[2],
                "alternativaD": alts[3],
                "respostaCorreta": letra,
            }
        )

    # dedupe per difficulty
    by_level: dict[int, list[dict]] = {1: [], 2: [], 3: []}
    used: set[str] = set()
    removed_dups = 0
    for p in polished:
        k = norm(p["enunciado"])
        if k in used:
            removed_dups += 1
            continue
        used.add(k)
        by_level[p["dificuldade"]].append(p)

    added = {1: 0, 2: 0, 3: 0}
    for dif, quota in LEVELS.items():
        have = len(by_level[dif])
        if have > quota:
            by_level[dif] = by_level[dif][:quota]
        elif have < quota:
            need = quota - have
            extra = expand_fillers(lang, dif, need, used)
            by_level[dif].extend(extra)
            added[dif] = need

    final = by_level[1] + by_level[2] + by_level[3]
    save(lang, final)

    # metrics
    sobre = sum(1 for p in final if p["enunciado"].startswith("Sobre "))
    oque_bad = sum(
        1
        for p in final
        if re.match(r"(?i)^O que [A-ZÁÉÍÓÚ]", p["enunciado"])
        and not re.match(
            r"(?i)^O que (é |o |a |os |as |um |uma |significa|representa|permite|indica)",
            p["enunciado"],
        )
    )
    resulta = sum(1 for p in final if re.search(r"(?i)resulta em\?", p["enunciado"]))
    int_bad = sum(1 for p in final if re.search(r"\bInt\b", p["enunciado"]))
    dups = len(final) - len({norm(p["enunciado"]) for p in final})
    return {
        "lang": lang,
        "total": len(final),
        "by_level": {d: len(by_level[d]) for d in LEVELS},
        "removed_dups": removed_dups,
        "added": added,
        "sobre": sobre,
        "oque_bad": oque_bad,
        "resulta": resulta,
        "int_bad": int_bad,
        "remaining_dups": dups,
    }


def main() -> None:
    reports = [process_lang(lang) for lang in ("java", "python", "cpp")]
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
