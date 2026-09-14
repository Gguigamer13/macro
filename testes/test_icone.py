"""Testes do gerador de ícone.

O .ico é montado byte a byte, então vale conferir se o arquivo sai mesmo no
formato que o Windows espera.
"""

import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ferramentas import gerar_icone  # noqa: E402


class TesteIcone(unittest.TestCase):
    def test_desenho_tem_o_tamanho_pedido(self):
        linhas = gerar_icone.desenhar(16)
        self.assertEqual(len(linhas), 16)
        self.assertTrue(all(len(linha) == 16 for linha in linhas))

    def test_o_meio_e_o_corpo_do_mouse_e_a_ponta_e_transparente(self):
        linhas = gerar_icone.desenhar(32)
        _r, _g, _b, alfa_centro = linhas[16][16]
        self.assertEqual(alfa_centro, 255, "o meio do ícone não pode ser transparente")
        self.assertEqual(linhas[0][0][3], 0, "o canto tem que ficar transparente")

    def test_ico_sai_no_formato_certo(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = os.path.join(pasta, "icone.ico")
            tamanhos = (16, 32, 256)
            gerar_icone.salvar_ico(destino, tamanhos)
            with open(destino, "rb") as arquivo:
                dados = arquivo.read()

            reservado, tipo, quantidade = struct.unpack("<HHH", dados[:6])
            self.assertEqual((reservado, tipo), (0, 1))       # 1 = ícone
            self.assertEqual(quantidade, len(tamanhos))

            for indice, tamanho in enumerate(tamanhos):
                inicio = 6 + indice * 16
                (largura, altura, cores, _res, planos, bits, bytes_imagem,
                 deslocamento) = struct.unpack("<BBBBHHII", dados[inicio:inicio + 16])
                esperado = 0 if tamanho >= 256 else tamanho   # 0 significa 256
                self.assertEqual((largura, altura), (esperado, esperado))
                self.assertEqual((cores, planos, bits), (0, 1, 32))
                self.assertLessEqual(deslocamento + bytes_imagem, len(dados),
                                     "a imagem aponta para fora do arquivo")
                # cada imagem começa com um cabeçalho BMP de 40 bytes
                cabecalho = struct.unpack("<Iii", dados[deslocamento:deslocamento + 12])
                self.assertEqual(cabecalho[0], 40)
                self.assertEqual(cabecalho[1], tamanho)
                self.assertEqual(cabecalho[2], tamanho * 2)   # imagem + máscara

    def test_png_de_previa(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = os.path.join(pasta, "previa.png")
            gerar_icone.salvar_png(destino, 32)
            with open(destino, "rb") as arquivo:
                dados = arquivo.read()
            self.assertEqual(dados[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(dados[12:16], b"IHDR")
            self.assertEqual(struct.unpack(">II", dados[16:24]), (32, 32))
            self.assertEqual(dados[-12:], b"\x00\x00\x00\x00IEND\xaeB`\x82")


if __name__ == "__main__":
    unittest.main(verbosity=2)
