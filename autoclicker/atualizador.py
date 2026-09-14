"""Busca e instala a última versão do programa direto do GitHub.

Só usa a biblioteca padrão (urllib + zipfile), então continua sem depender de
nada instalado. O arquivo versao.json, na raiz do repositório, é quem diz qual
é a versão publicada.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Callable, Optional

from . import __version__

REPOSITORIO = "Gguigamer13/macro"

# Procura nesta ordem: assim continua funcionando depois que a branch de
# desenvolvimento for juntada na principal.
BRANCHES = ("main", "master", "claude/auto-click-macro-page-select-d8dwj1")

URL_API = "https://api.github.com/repos/{repo}"
URL_VERSAO = "https://raw.githubusercontent.com/{repo}/{branch}/versao.json"
URL_PACOTE = "https://codeload.github.com/{repo}/zip/refs/heads/{branch}"
URL_PAGINA = "https://github.com/{repo}"

PASTA_BACKUP = "versao-anterior"
PASTA_ATUALIZACAO = "atualizacao"

# não faz sentido copiar isso por cima da instalação de ninguém
IGNORADOS = {".git", ".github", "__pycache__", "build", "dist", ".gitignore"}


class ErroDeAtualizacao(RuntimeError):
    """Algo deu errado ao procurar ou instalar a atualização."""


@dataclass
class Atualizacao:
    versao: str
    notas: str
    data: str
    branch: str
    instalada: str
    candidatas: tuple = ()

    @property
    def mais_nova(self) -> bool:
        return comparar_versoes(self.versao, self.instalada) > 0

    @property
    def url_pacote(self) -> str:
        return URL_PACOTE.format(repo=REPOSITORIO, branch=self.branch)

    @property
    def url_pagina(self) -> str:
        return URL_PAGINA.format(repo=REPOSITORIO)


def versao_instalada() -> str:
    return __version__


def comparar_versoes(uma: str, outra: str) -> int:
    """1 se 'uma' for mais nova, -1 se for mais velha, 0 se forem iguais."""
    def partes(texto: str) -> tuple:
        numeros = []
        for pedaco in str(texto).strip().lstrip("vV").split("."):
            digitos = "".join(c for c in pedaco if c.isdigit())
            numeros.append(int(digitos) if digitos else 0)
        return tuple(numeros)

    a, b = partes(uma), partes(outra)
    tamanho = max(len(a), len(b))
    a += (0,) * (tamanho - len(a))
    b += (0,) * (tamanho - len(b))
    return (a > b) - (a < b)


def esta_congelado() -> bool:
    """True quando o programa está rodando como .exe (PyInstaller)."""
    return bool(getattr(sys, "frozen", False))


def pasta_do_programa() -> str:
    """Pasta onde o programa está instalado."""
    if esta_congelado():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------------------
# Rede
# --------------------------------------------------------------------------


def _baixar(url: str, tempo_limite: int = 15) -> bytes:
    pedido = urllib.request.Request(url, headers={
        "User-Agent": f"AutoClicker/{__version__}",
        "Accept": "*/*",
    })
    try:
        with urllib.request.urlopen(pedido, timeout=tempo_limite) as resposta:
            return resposta.read()
    except urllib.error.HTTPError as erro:
        raise ErroDeAtualizacao(f"O GitHub respondeu {erro.code} em {url}") from erro
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        raise ErroDeAtualizacao(
            "Não consegui falar com o GitHub. Verifique a internet.") from erro


def _branch_padrao(tempo_limite: int = 10) -> Optional[str]:
    """Pergunta ao GitHub qual é a branch principal do repositório.

    Vale a pergunta: o endereço "raw" aceita master como apelido da branch
    padrao, mas o download do .zip so aceita o nome de verdade - entao adivinhar
    o nome daria versao certa e pacote inexistente.
    """
    try:
        dados = json.loads(
            _baixar(URL_API.format(repo=REPOSITORIO), tempo_limite).decode("utf-8"))
    except (ErroDeAtualizacao, ValueError, UnicodeDecodeError):
        return None
    branch = str(dados.get("default_branch", "")).strip()
    return branch or None


def _branches_candidatas(tempo_limite: int) -> list:
    candidatas = []
    padrao = _branch_padrao(min(tempo_limite, 10))
    if padrao:
        candidatas.append(padrao)
    for branch in BRANCHES:
        if branch not in candidatas:
            candidatas.append(branch)
    return candidatas


def procurar_atualizacao(tempo_limite: int = 15) -> Atualizacao:
    """Lê o versao.json publicado e devolve o que encontrou."""
    ultimo_erro: Optional[Exception] = None
    candidatas = _branches_candidatas(tempo_limite)
    for branch in candidatas:
        url = URL_VERSAO.format(repo=REPOSITORIO, branch=branch)
        try:
            dados = json.loads(_baixar(url, tempo_limite).decode("utf-8"))
        except ErroDeAtualizacao as erro:
            ultimo_erro = erro
            continue
        except (ValueError, UnicodeDecodeError):
            ultimo_erro = ErroDeAtualizacao("O arquivo de versão veio corrompido.")
            continue
        versao = str(dados.get("versao", "")).strip()
        if not versao:
            ultimo_erro = ErroDeAtualizacao("O arquivo de versão não traz a versão.")
            continue
        return Atualizacao(versao=versao, notas=str(dados.get("notas", "")).strip(),
                           data=str(dados.get("data", "")).strip(), branch=branch,
                           instalada=versao_instalada(),
                           candidatas=tuple(candidatas))
    raise ultimo_erro or ErroDeAtualizacao("Não encontrei a versão publicada.")


def baixar_pacote(atualizacao: Atualizacao, pasta: str,
                  tempo_limite: int = 60) -> str:
    """Baixa o .zip do programa e devolve o caminho do arquivo.

    Tenta a branch de onde veio a versao e, se ela nao existir como ref de
    verdade (caso do apelido "master"), tenta as outras da lista.
    """
    destino = os.path.join(pasta, "autoclicker-atualizacao.zip")
    tentativas = [atualizacao.branch] + [b for b in atualizacao.candidatas
                                         if b != atualizacao.branch]
    ultimo_erro: Optional[Exception] = None
    for branch in tentativas:
        url = URL_PACOTE.format(repo=REPOSITORIO, branch=branch)
        try:
            dados = _baixar(url, tempo_limite)
        except ErroDeAtualizacao as erro:
            ultimo_erro = erro
            continue
        with open(destino, "wb") as arquivo:
            arquivo.write(dados)
        return destino
    raise ultimo_erro or ErroDeAtualizacao("Não consegui baixar a nova versão.")


# --------------------------------------------------------------------------
# Instalação
# --------------------------------------------------------------------------


def _extrair_com_seguranca(caminho_zip: str, destino: str) -> str:
    """Extrai o pacote conferindo cada caminho e devolve a pasta de dentro.

    A conferência evita o truque do 'zip slip', em que um arquivo do pacote
    aponta para fora da pasta (../..) e sobrescreve o que não devia.
    """
    raiz_real = os.path.realpath(destino)
    try:
        with zipfile.ZipFile(caminho_zip) as pacote:
            for membro in pacote.namelist():
                alvo = os.path.realpath(os.path.join(destino, membro))
                if not (alvo == raiz_real or alvo.startswith(raiz_real + os.sep)):
                    raise ErroDeAtualizacao(
                        f"O pacote baixado tem um arquivo suspeito: {membro}")
            pacote.extractall(destino)
    except zipfile.BadZipFile as erro:
        raise ErroDeAtualizacao("O pacote baixado está corrompido.") from erro

    pastas = [nome for nome in os.listdir(destino)
              if os.path.isdir(os.path.join(destino, nome))]
    raiz = os.path.join(destino, pastas[0]) if len(pastas) == 1 else destino
    if not os.path.exists(os.path.join(raiz, "autoclicker", "gui.py")):
        raise ErroDeAtualizacao(
            "O pacote baixado não parece ser o Auto Clicker.")
    return raiz


def _arquivos_do_pacote(raiz: str) -> list:
    """Lista os arquivos que devem ser copiados, em caminho relativo."""
    encontrados = []
    for pasta, subpastas, arquivos in os.walk(raiz):
        subpastas[:] = [nome for nome in subpastas if nome not in IGNORADOS]
        for arquivo in arquivos:
            if arquivo in IGNORADOS or arquivo.endswith(".pyc"):
                continue
            completo = os.path.join(pasta, arquivo)
            encontrados.append(os.path.relpath(completo, raiz))
    return sorted(encontrados)


def instalar_pacote(caminho_zip: str, destino: str,
                    aviso: Optional[Callable[[str], None]] = None) -> list:
    """Copia os arquivos do pacote por cima da instalação, com backup.

    Se qualquer cópia falhar no meio do caminho, tudo o que já tinha sido
    trocado volta ao que era antes.
    """
    os.makedirs(destino, exist_ok=True)
    backup = os.path.join(destino, PASTA_BACKUP)
    if os.path.exists(backup):
        shutil.rmtree(backup, ignore_errors=True)

    copiados: list = []
    with tempfile.TemporaryDirectory() as temporaria:
        raiz = _extrair_com_seguranca(caminho_zip, temporaria)
        for relativo in _arquivos_do_pacote(raiz):
            origem = os.path.join(raiz, relativo)
            alvo = os.path.join(destino, relativo)
            try:
                if os.path.exists(alvo):
                    guardado = os.path.join(backup, relativo)
                    os.makedirs(os.path.dirname(guardado), exist_ok=True)
                    shutil.copy2(alvo, guardado)
                os.makedirs(os.path.dirname(alvo), exist_ok=True)
                shutil.copy2(origem, alvo)
                copiados.append(relativo)
            except OSError as erro:
                _desfazer(backup, destino, copiados)
                raise ErroDeAtualizacao(
                    f"Não consegui gravar {relativo}: {erro}.\n"
                    "Nada foi alterado. Feche o programa e tente de novo, ou "
                    "rode como administrador.") from erro
        if aviso:
            aviso(f"{len(copiados)} arquivos atualizados.")
    return copiados


def _desfazer(backup: str, destino: str, copiados: list) -> None:
    """Devolve os arquivos guardados no backup para o lugar."""
    for relativo in copiados:
        guardado = os.path.join(backup, relativo)
        if os.path.exists(guardado):
            try:
                shutil.copy2(guardado, os.path.join(destino, relativo))
            except OSError:
                pass


def atualizar(atualizacao: Atualizacao,
              aviso: Optional[Callable[[str], None]] = None) -> str:
    """Baixa e instala. Devolve a mensagem para mostrar ao usuário."""
    with tempfile.TemporaryDirectory() as temporaria:
        if aviso:
            aviso("Baixando a nova versão...")
        pacote = baixar_pacote(atualizacao, temporaria)
        if aviso:
            aviso("Instalando...")

        if esta_congelado():
            # o .exe tem o programa embutido: trocar os .py não muda nada nele.
            # Então o código novo vai para uma pasta ao lado, pronto para gerar
            # um .exe novo com o criar_exe.bat.
            destino = os.path.join(pasta_do_programa(), PASTA_ATUALIZACAO)
            shutil.rmtree(destino, ignore_errors=True)
            instalar_pacote(pacote, destino, aviso)
            return (f"Versão {atualizacao.versao} baixada em:\n{destino}\n\n"
                    "Como você está usando o .exe, abra essa pasta e rode o "
                    "criar_exe.bat para gerar o executável novo.")

        destino = pasta_do_programa()
        instalar_pacote(pacote, destino, aviso)
        return (f"Versão {atualizacao.versao} instalada!\n\n"
                "Feche e abra o Auto Clicker para começar a usar.\n"
                f"A versão anterior ficou guardada em {PASTA_BACKUP}.")
