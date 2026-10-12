"""Leitura de YAML com a linha de origem de cada valor.

Base das mensagens de erro "arquivo:linha" do catálogo (R14).
"""

import yaml

from esquema import formata_caminho

# O carregador em C é bem mais rápido; o puro Python dá o mesmo resultado.
CARREGADOR = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

ALINHAMENTO = "alinhe a linha com os campos vizinhos (2 espaços por nível, só espaços)"

# Dicas em português para as mensagens do PyYAML, que vêm em inglês. A chave é
# um trecho da mensagem, igual no carregador em C e no puro Python.
DICAS = (
    ("mapping values are not allowed",
     f"texto com ': ' precisa ficar entre aspas simples (descricao: 'Consulta: CPF'); se não for isso, {ALINHAMENTO}"),
    ("cannot start any token",
     "texto que começa com crase, @ ou % precisa ficar entre aspas simples; indente só com espaços, nunca com tabulação"),
    ("alphabetic or numeric character", "texto que começa com * ou & precisa ficar entre aspas simples"),
    ("undefined alias", "texto que começa com * ou & precisa ficar entre aspas simples"),
    ("constructor for the tag", "texto que começa com ! precisa ficar entre aspas simples"),
    ("did not find expected key", f"texto que começa com [ ou {{ precisa ficar entre aspas simples; se não for isso, {ALINHAMENTO}"),
    ("expected <block end>", f"texto que começa com [ ou {{ precisa ficar entre aspas simples; se não for isso, {ALINHAMENTO}"),
    ("expected '-' indicator", ALINHAMENTO),
    ("end of stream", "aspas abertas e não fechadas; para um apóstrofo dentro de aspas simples, escreva duas aspas ('')"),
    ("could not find expected ':'", "falta ': ' depois do nome do campo, ou um texto longo quebrou a linha sem aspas"),
)


def dica(problema):
    """Dica em português para a mensagem do PyYAML, ou "" se não houver."""
    for trecho, texto in DICAS:
        if trecho in problema:
            return texto
    return ""


def _invalido(rotulo, linha, problema):
    texto = dica(problema)
    sufixo = f". Dica: {texto}" if texto else ""
    return f"{rotulo}:{linha}: YAML inválido: {problema}{sufixo}"


def le_yaml(texto, rotulo):
    """Interpreta YAML guardando a linha de cada valor.

    Retorna (dados, linhas, erros). 'linhas' mapeia o caminho de cada valor,
    como ("fontes", 0, "links", 1, "url"), para a linha (a partir de 1).
    """
    try:
        raiz = yaml.compose(texto, Loader=CARREGADOR)
    except yaml.YAMLError as erro:
        marca = getattr(erro, "problem_mark", None) or getattr(erro, "context_mark", None)
        if "quoted scalar" in (getattr(erro, "context", None) or ""):
            marca = erro.context_mark  # aspas sem fechar: a linha útil é a que abre as aspas
        linha = marca.line + 1 if marca else 1
        problema = getattr(erro, "problem", None) or str(erro)
        return None, {}, [_invalido(rotulo, linha, problema)]
    if raiz is None:
        return None, {}, [f"{rotulo}:1: arquivo vazio"]
    linhas, erros = {}, []
    construtor = yaml.constructor.SafeConstructor()
    try:
        dados = _converte(raiz, (), linhas, erros, rotulo, construtor)
    except _ErroNo as erro:
        return None, {}, erros + [erro.args[0]]
    return dados, linhas, erros


class _ErroNo(Exception):
    pass


def _constroi(no, construtor, rotulo):
    try:
        return construtor.construct_object(no, deep=True)
    except yaml.YAMLError as erro:
        problema = getattr(erro, "problem", None) or str(erro)
        raise _ErroNo(_invalido(rotulo, no.start_mark.line + 1, problema)) from None
    except TypeError:
        raise _ErroNo(f"{rotulo}:{no.start_mark.line + 1}: YAML inválido: chave não pode ser lista ou mapa") from None


def _converte(no, caminho, linhas, erros, rotulo, construtor):
    linhas[caminho] = no.start_mark.line + 1
    if isinstance(no, yaml.MappingNode):
        resultado = {}
        for no_chave, no_valor in no.value:
            chave = _constroi(no_chave, construtor, rotulo)
            try:
                repetida = chave in resultado
            except TypeError:
                raise _ErroNo(f"{rotulo}:{no_chave.start_mark.line + 1}: YAML inválido: "
                              "chave não pode ser lista ou mapa") from None
            if repetida:
                erros.append(f"{rotulo}:{no_chave.start_mark.line + 1}: chave '{chave}' repetida")
                continue
            resultado[chave] = _converte(no_valor, caminho + (chave,), linhas, erros, rotulo, construtor)
        return resultado
    if isinstance(no, yaml.SequenceNode):
        return [
            _converte(item, caminho + (i,), linhas, erros, rotulo, construtor)
            for i, item in enumerate(no.value)
        ]
    return _constroi(no, construtor, rotulo)


def linha_de(linhas, caminho):
    """Linha do valor em 'caminho' ou, se ele não existe, do objeto mais próximo."""
    caminho = tuple(caminho)
    while caminho and caminho not in linhas:
        caminho = caminho[:-1]
    return linhas.get(caminho, 1)


def erro_em(rotulo, linhas, caminho, mensagem):
    return f"{rotulo}:{linha_de(linhas, caminho)}: {formata_caminho(caminho)}: {mensagem}"
