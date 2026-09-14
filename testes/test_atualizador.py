"""Testes da atualização pelo GitHub.

Nenhum teste acessa a internet: a função que baixa é trocada por um dublê e o
pacote .zip é montado na hora, numa pasta temporária.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autoclicker import atualizador  # noqa: E402


def montar_pacote(caminho_zip: str, versao: str = "9.9.9",
                  conteudo: str = "novo") -> None:
    """Monta um .zip igual ao que o GitHub entrega: tudo dentro de uma pasta."""
    raiz = "macro-branch"
    with zipfile.ZipFile(caminho_zip, "w") as pacote:
        pacote.writestr(f"{raiz}/autoclicker/gui.py", f"# {conteudo}\n")
        pacote.writestr(f"{raiz}/autoclicker/__init__.py",
                        f'__version__ = "{versao}"\n')
        pacote.writestr(f"{raiz}/README.md", f"{conteudo}\n")
        pacote.writestr(f"{raiz}/versao.json", json.dumps({"versao": versao}))
        pacote.writestr(f"{raiz}/__pycache__/gui.pyc", "lixo")      # nao copiar
        pacote.writestr(f"{raiz}/.git/config", "lixo")              # nao copiar


class TesteComparacaoDeVersoes(unittest.TestCase):
    def test_ordem_das_versoes(self):
        self.assertEqual(atualizador.comparar_versoes("1.2.0", "1.1.9"), 1)
        self.assertEqual(atualizador.comparar_versoes("1.1.0", "1.1.0"), 0)
        self.assertEqual(atualizador.comparar_versoes("1.2.0", "1.10.0"), -1)
        self.assertEqual(atualizador.comparar_versoes("v2.0", "1.9.9"), 1)
        self.assertEqual(atualizador.comparar_versoes("1.1", "1.1.0"), 0)

    def test_versao_estranha_nao_quebra(self):
        self.assertEqual(atualizador.comparar_versoes("abc", "0.0.0"), 0)


class TesteProcura(unittest.TestCase):
    def setUp(self):
        self.original = atualizador._baixar
        self.pedidos = []

    def tearDown(self):
        atualizador._baixar = self.original

    def _responder(self, respostas):
        def falso(url, tempo_limite=15):
            self.pedidos.append(url)
            for pedaco, resposta in respostas.items():
                if pedaco in url:
                    if isinstance(resposta, Exception):
                        raise resposta
                    return resposta.encode("utf-8")
            raise atualizador.ErroDeAtualizacao("404")
        atualizador._baixar = falso

    def test_usa_a_primeira_branch_que_responder(self):
        self._responder({"/master/": json.dumps({"versao": "9.9.9",
                                                 "notas": "coisas novas"})})
        info = atualizador.procurar_atualizacao()
        self.assertEqual(info.versao, "9.9.9")
        self.assertEqual(info.branch, "master")
        self.assertEqual(info.notas, "coisas novas")
        self.assertTrue(info.mais_nova)
        self.assertIn("/main/", self.pedidos[0])  # tentou a principal primeiro

    def test_avisa_quando_ja_esta_atualizado(self):
        self._responder({"/main/": json.dumps(
            {"versao": atualizador.versao_instalada()})})
        info = atualizador.procurar_atualizacao()
        self.assertFalse(info.mais_nova)

    def test_erro_claro_quando_nao_acha_nada(self):
        self._responder({})
        with self.assertRaises(atualizador.ErroDeAtualizacao):
            atualizador.procurar_atualizacao()

    def test_json_corrompido_nao_derruba(self):
        self._responder({"/main/": "isso nao e json"})
        with self.assertRaises(atualizador.ErroDeAtualizacao):
            atualizador.procurar_atualizacao()


class TesteInstalacao(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.destino = os.path.join(self.pasta, "programa")
        os.makedirs(os.path.join(self.destino, "autoclicker"))
        with open(os.path.join(self.destino, "README.md"), "w") as arquivo:
            arquivo.write("versao antiga\n")
        with open(os.path.join(self.destino, "autoclicker", "gui.py"), "w") as arquivo:
            arquivo.write("# antigo\n")
        self.zip = os.path.join(self.pasta, "pacote.zip")
        montar_pacote(self.zip)

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def _ler(self, *partes):
        with open(os.path.join(self.destino, *partes), encoding="utf-8") as arquivo:
            return arquivo.read()

    def test_troca_os_arquivos_e_guarda_o_backup(self):
        copiados = atualizador.instalar_pacote(self.zip, self.destino)
        self.assertIn("README.md", copiados)
        self.assertEqual(self._ler("README.md"), "novo\n")
        self.assertEqual(self._ler("autoclicker", "gui.py"), "# novo\n")
        guardado = os.path.join(self.destino, atualizador.PASTA_BACKUP, "README.md")
        with open(guardado, encoding="utf-8") as arquivo:
            self.assertEqual(arquivo.read(), "versao antiga\n")

    def test_nao_copia_cache_nem_pasta_do_git(self):
        copiados = atualizador.instalar_pacote(self.zip, self.destino)
        self.assertFalse([c for c in copiados if "__pycache__" in c or ".git" in c])
        self.assertFalse(os.path.exists(os.path.join(self.destino, "__pycache__")))
        self.assertFalse(os.path.exists(os.path.join(self.destino, ".git")))

    def test_se_falhar_no_meio_volta_tudo_como_estava(self):
        original = atualizador.shutil.copy2
        chamadas = []

        def copiar(origem, destino, *args, **kwargs):
            chamadas.append(destino)
            # deixa passar o backup e a primeira troca, depois quebra
            if len(chamadas) > 3:
                raise OSError("disco cheio")
            return original(origem, destino, *args, **kwargs)

        atualizador.shutil.copy2 = copiar
        try:
            with self.assertRaises(atualizador.ErroDeAtualizacao) as caso:
                atualizador.instalar_pacote(self.zip, self.destino)
            self.assertIn("Nada foi alterado", str(caso.exception))
        finally:
            atualizador.shutil.copy2 = original
        # os arquivos que chegaram a ser trocados voltaram ao conteúdo antigo
        self.assertEqual(self._ler("autoclicker", "gui.py"), "# antigo\n")

    def test_recusa_pacote_que_escapa_da_pasta(self):
        """Um .zip malicioso não pode gravar fora da pasta de destino."""
        perigoso = os.path.join(self.pasta, "perigoso.zip")
        with zipfile.ZipFile(perigoso, "w") as pacote:
            pacote.writestr("macro-branch/autoclicker/gui.py", "# ok\n")
            pacote.writestr("macro-branch/../../invadiu.txt", "oi")
        with self.assertRaises(atualizador.ErroDeAtualizacao) as caso:
            atualizador.instalar_pacote(perigoso, self.destino)
        self.assertIn("suspeito", str(caso.exception))
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "invadiu.txt")))

    def test_recusa_pacote_que_nao_e_o_programa(self):
        outro = os.path.join(self.pasta, "outro.zip")
        with zipfile.ZipFile(outro, "w") as pacote:
            pacote.writestr("qualquer-coisa/leiame.txt", "nada a ver")
        with self.assertRaises(atualizador.ErroDeAtualizacao) as caso:
            atualizador.instalar_pacote(outro, self.destino)
        self.assertIn("não parece ser o Auto Clicker", str(caso.exception))

    def test_pacote_corrompido_da_mensagem_clara(self):
        quebrado = os.path.join(self.pasta, "quebrado.zip")
        with open(quebrado, "wb") as arquivo:
            arquivo.write(b"isso nao e um zip")
        with self.assertRaises(atualizador.ErroDeAtualizacao) as caso:
            atualizador.instalar_pacote(quebrado, self.destino)
        self.assertIn("corrompido", str(caso.exception))


class TesteVersaoPublicada(unittest.TestCase):
    def test_versao_json_bate_com_a_do_programa(self):
        """Se esquecer de subir uma das duas, a atualização mente a versão."""
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(raiz, "versao.json"), encoding="utf-8") as arquivo:
            publicada = json.load(arquivo)
        self.assertEqual(publicada["versao"], atualizador.versao_instalada())
        self.assertTrue(publicada.get("notas"), "escreva o que mudou em versao.json")


if __name__ == "__main__":
    unittest.main(verbosity=2)
