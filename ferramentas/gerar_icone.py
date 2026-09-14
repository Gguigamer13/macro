"""Desenha o ícone do Auto Clicker e salva em .ico (e, se pedirem, em .png).

Escrito na mão, sem nenhuma biblioteca de imagem: o .ico é montado byte a byte,
então funciona em qualquer Python novo, no Windows ou em qualquer outro sistema.

Uso:
    python ferramentas/gerar_icone.py icone.ico
    python ferramentas/gerar_icone.py icone.ico --png previa.png
"""

from __future__ import annotations

import math
import struct
import sys
import zlib

# mesmas cores da interface
AZUL_BEBE = (169, 214, 242)
AZUL_MEDIO = (124, 188, 228)
AZUL_ESCURO = (47, 106, 150)
BRANCO_GELO = (251, 253, 255)

TAMANHOS = (16, 24, 32, 48, 64, 128, 256)
AMOSTRAS = 3  # 3x3 pontos por pixel, para as bordas não ficarem serrilhadas


def _sobrepor(base: tuple, cor: tuple, alfa: float) -> tuple:
    """Coloca 'cor' por cima de 'base' com a opacidade dada."""
    return tuple(base[i] + (cor[i] - base[i]) * alfa for i in range(3)) + (
        max(base[3], alfa),)


def _capsula(x: float, y: float, cx: float, cy: float, meia_largura: float,
             meia_altura: float) -> float:
    """Distância até a borda do corpo do mouse (negativa = dentro)."""
    raio = meia_largura
    dy = max(abs(y - cy) - (meia_altura - raio), 0.0)
    return math.hypot(abs(x - cx), dy) - raio


def _cor_do_ponto(x: float, y: float) -> tuple:
    """Cor (r, g, b, a) de um ponto, em coordenadas de 0.0 a 1.0."""
    cor = (255.0, 255.0, 255.0, 0.0)  # transparente

    # fundo redondo, com um leve degradê de cima para baixo
    dist_fundo = math.hypot(x - 0.5, y - 0.5) - 0.48
    if dist_fundo < 0:
        mistura = min(max(y, 0.0), 1.0)
        fundo = tuple(AZUL_BEBE[i] + (AZUL_MEDIO[i] - AZUL_BEBE[i]) * mistura
                      for i in range(3))
        cor = _sobrepor(cor, fundo, 1.0)
        if dist_fundo > -0.035:  # aro mais escuro na beirada
            cor = _sobrepor(cor, AZUL_MEDIO, 1.0)
    else:
        return cor

    # corpo do mouse
    dist = _capsula(x, y, 0.5, 0.5, 0.165, 0.255)
    if dist < 0:
        cor = _sobrepor(cor, BRANCO_GELO, 1.0)
    if abs(dist) < 0.026:  # contorno
        cor = _sobrepor(cor, AZUL_ESCURO, 1.0)

    # risco vertical e horizontal que separam os botões
    if dist < -0.01:
        if abs(x - 0.5) < 0.016 and y < 0.492:
            cor = _sobrepor(cor, AZUL_ESCURO, 1.0)
        if abs(y - 0.492) < 0.016:
            cor = _sobrepor(cor, AZUL_ESCURO, 1.0)
    return cor


def desenhar(tamanho: int) -> list:
    """Gera a imagem como lista de linhas de pixels (r, g, b, a) de 0 a 255."""
    linhas = []
    for py in range(tamanho):
        linha = []
        for px in range(tamanho):
            soma = [0.0, 0.0, 0.0, 0.0]
            for sy in range(AMOSTRAS):
                for sx in range(AMOSTRAS):
                    x = (px + (sx + 0.5) / AMOSTRAS) / tamanho
                    y = (py + (sy + 0.5) / AMOSTRAS) / tamanho
                    ponto = _cor_do_ponto(x, y)
                    for i in range(4):
                        soma[i] += ponto[i]
            total = AMOSTRAS * AMOSTRAS
            r, g, b, a = (valor / total for valor in soma)
            linha.append((round(r), round(g), round(b), round(a * 255)))
        linhas.append(linha)
    return linhas


def _imagem_ico(linhas: list) -> bytes:
    """Uma imagem dentro do .ico: cabeçalho BMP + pixels BGRA + máscara."""
    tamanho = len(linhas)
    cabecalho = struct.pack("<IiiHHIIiiII", 40, tamanho, tamanho * 2, 1, 32, 0,
                            tamanho * tamanho * 4, 0, 0, 0, 0)
    pixels = bytearray()
    for linha in reversed(linhas):  # BMP guarda de baixo para cima
        for r, g, b, a in linha:
            pixels += bytes((b, g, r, a))
    # máscara AND: 1 bit por pixel, cada linha completada até múltiplo de 4 bytes
    bytes_por_linha = ((tamanho + 31) // 32) * 4
    mascara = bytearray(bytes_por_linha * tamanho)
    return bytes(cabecalho) + bytes(pixels) + bytes(mascara)


def salvar_ico(caminho: str, tamanhos=TAMANHOS) -> None:
    imagens = [_imagem_ico(desenhar(t)) for t in tamanhos]
    cabecalho = struct.pack("<HHH", 0, 1, len(imagens))
    deslocamento = len(cabecalho) + 16 * len(imagens)
    entradas = b""
    for tamanho, imagem in zip(tamanhos, imagens):
        lado = 0 if tamanho >= 256 else tamanho  # 0 quer dizer 256 no formato
        entradas += struct.pack("<BBBBHHII", lado, lado, 0, 0, 1, 32,
                                len(imagem), deslocamento)
        deslocamento += len(imagem)
    with open(caminho, "wb") as arquivo:
        arquivo.write(cabecalho + entradas + b"".join(imagens))


def salvar_png(caminho: str, tamanho: int = 256) -> None:
    """PNG simples, só para conferir o desenho com os olhos."""
    linhas = desenhar(tamanho)
    dados = bytearray()
    for linha in linhas:
        dados.append(0)  # filtro "nenhum"
        for r, g, b, a in linha:
            dados += bytes((r, g, b, a))

    def bloco(nome: bytes, conteudo: bytes) -> bytes:
        return (struct.pack(">I", len(conteudo)) + nome + conteudo
                + struct.pack(">I", zlib.crc32(nome + conteudo) & 0xFFFFFFFF))

    cabecalho = struct.pack(">IIBBBBB", tamanho, tamanho, 8, 6, 0, 0, 0)
    with open(caminho, "wb") as arquivo:
        arquivo.write(b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", cabecalho)
                      + bloco(b"IDAT", zlib.compress(bytes(dados), 9))
                      + bloco(b"IEND", b""))


def main(argumentos: list) -> int:
    destino = argumentos[0] if argumentos else "icone.ico"
    salvar_ico(destino)
    print(f"icone gerado: {destino}")
    if "--png" in argumentos:
        png = argumentos[argumentos.index("--png") + 1]
        salvar_png(png)
        print(f"previa gerada: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
