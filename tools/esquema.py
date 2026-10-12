"""Validador mínimo de JSON Schema, só com a biblioteca padrão.

Cobre o subconjunto usado em data/schemas/catalogo.schema.json e
data/schemas/categorias.schema.json: type, properties, required,
additionalProperties (booleano), items, enum, pattern, minLength,
minItems e uniqueItems. Palavras-chave fora dessa lista são ignoradas.

Cada erro é um par (caminho, mensagem). O caminho é uma tupla de chaves e
índices até o valor com problema, por exemplo ("fontes", 3, "links", 0, "url"),
e serve para achar a linha no arquivo YAML de origem.
"""

import re

TIPOS = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def _tem_tipo(valor, tipo):
    if tipo == "integer":
        return isinstance(valor, int) and not isinstance(valor, bool)
    return isinstance(valor, TIPOS[tipo])


def _nome_tipo(valor):
    for nome, classe in TIPOS.items():
        if isinstance(valor, classe):
            return nome
    if isinstance(valor, int):
        return "integer"
    return type(valor).__name__


def valida(valor, esquema, caminho=()):
    """Retorna a lista de erros (caminho, mensagem) de valor contra esquema."""
    erros = []
    tipo = esquema.get("type")
    if tipo is not None:
        tipos = tipo if isinstance(tipo, list) else [tipo]
        if not any(_tem_tipo(valor, t) for t in tipos):
            esperado = " ou ".join(tipos)
            erros.append((caminho, f"tipo {_nome_tipo(valor)}, esperado {esperado}"))
            return erros

    if "enum" in esquema and valor not in esquema["enum"]:
        erros.append((caminho, f"valor {valor!r} fora da lista permitida"))

    if isinstance(valor, str):
        if len(valor) < esquema.get("minLength", 0):
            erros.append((caminho, "texto vazio"))
        padrao = esquema.get("pattern")
        if padrao and not re.search(padrao, valor):
            erros.append((caminho, f"valor {valor!r} não segue o padrão {padrao}"))

    if isinstance(valor, dict):
        for campo in esquema.get("required", []):
            if campo not in valor:
                erros.append((caminho, f"campo obrigatório '{campo}' ausente"))
        propriedades = esquema.get("properties", {})
        for campo, sub in valor.items():
            if campo in propriedades:
                erros.extend(valida(sub, propriedades[campo], caminho + (campo,)))
            elif esquema.get("additionalProperties") is False:
                erros.append((caminho + (campo,), f"campo '{campo}' não permitido"))

    if isinstance(valor, list):
        if len(valor) < esquema.get("minItems", 0):
            erros.append((caminho, f"lista com {len(valor)} itens, mínimo {esquema['minItems']}"))
        if esquema.get("uniqueItems"):
            vistos = []
            for i, item in enumerate(valor):
                if item in vistos:
                    erros.append((caminho + (i,), f"item repetido {item!r}"))
                vistos.append(item)
        if "items" in esquema:
            for i, item in enumerate(valor):
                erros.extend(valida(item, esquema["items"], caminho + (i,)))

    return erros


def formata_caminho(caminho):
    """("fontes", 3, "links", 0) -> "fontes[3].links[0]"."""
    texto = ""
    for parte in caminho:
        if isinstance(parte, int):
            texto += f"[{parte}]"
        else:
            texto += f".{parte}" if texto else str(parte)
    return texto or "(raiz)"
