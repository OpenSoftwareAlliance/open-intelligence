"""Leitura de YAML com a linha de origem de cada valor.

Base das mensagens de erro "arquivo:linha" do catálogo (R14).
"""

import yaml

from esquema import formata_caminho

# O carregador em C é bem mais rápido; o puro Python dá o mesmo resultado.
CARREGADOR = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def le_yaml(texto, rotulo):
    """Interpreta YAML guardando a linha de cada valor.

    Retorna (dados, linhas, erros). 'linhas' mapeia o caminho de cada valor,
    como ("fontes", 0, "links", 1, "url"), para a linha (a partir de 1).
    """
    try:
        raiz = yaml.compose(texto, Loader=CARREGADOR)
    except yaml.YAMLError as erro:
        marca = getattr(erro, "problem_mark", None) or getattr(erro, "context_mark", None)
        linha = marca.line + 1 if marca else 1
        problema = getattr(erro, "problem", None) or str(erro)
        return None, {}, [f"{rotulo}:{linha}: YAML inválido: {problema}"]
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
        raise _ErroNo(f"{rotulo}:{no.start_mark.line + 1}: YAML inválido: {problema}") from None
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
