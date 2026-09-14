"""Testes da interface.

A janela é montada de verdade, mas o teclado global e o envio de cliques são
substituídos por dublês — nada é clicado e nenhum atalho é registrado.
Se o sistema não tiver tela disponível, os testes são pulados.
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import tkinter as tk
except ImportError:  # pragma: no cover
    tk = None

from autoclicker import config, engine  # noqa: E402

if tk is not None:
    from autoclicker import gui


class AtalhosFalsos:
    """Substitui o registrador de atalhos globais do Windows."""

    def __init__(self, on_error=None):
        self.ativos = {}

    def set_hotkeys(self, hotkeys):
        self.ativos = dict(hotkeys)

    def stop(self):
        self.ativos = {}


class SenderFalso(engine.Sender):
    def __init__(self):
        self.cliques = 0

    def down(self):
        self.cliques += 1

    def up(self):
        pass


@unittest.skipIf(tk is None, "tkinter não está instalado")
class TesteInterface(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as erro:  # sem tela (servidor headless)
            raise unittest.SkipTest(f"sem interface gráfica disponível: {erro}")
        self.root.withdraw()

        self.alertas = []
        self._originais = (gui.HotkeyListener, gui.messagebox.showerror,
                           gui.messagebox.showwarning, gui.messagebox.askyesno,
                           engine.build_sender, config.salvar, config.carregar)
        gui.HotkeyListener = AtalhosFalsos
        gui.messagebox.showerror = lambda *a, **k: self.alertas.append(("erro", a[1]))
        gui.messagebox.showwarning = lambda *a, **k: self.alertas.append(("aviso", a[1]))
        gui.messagebox.askyesno = lambda *a, **k: False
        config.carregar = lambda: dict(config.PADRAO)
        self.salvo = {}
        config.salvar = self.salvo.update

        self.sender = SenderFalso()
        engine.build_sender = lambda _ajustes: self.sender
        self.app = gui.AutoClickerApp(self.root)

    def tearDown(self):
        self.app.encerrar()
        (gui.HotkeyListener, gui.messagebox.showerror, gui.messagebox.showwarning,
         gui.messagebox.askyesno, engine.build_sender, config.salvar,
         config.carregar) = self._originais
        self.root.destroy()

    def _bombear(self, segundos=2.0, ate=None):
        """Roda o laço da interface por um tempo (ou até a condição acontecer)."""
        limite = time.time() + segundos
        while time.time() < limite:
            self.root.update()
            if ate and ate():
                return True
            time.sleep(0.02)
        return False

    # -- montagem --------------------------------------------------------

    def test_a_janela_abre_parada(self):
        self.assertEqual(self.root.title(), "Auto Clicker")
        self.assertEqual(self.app.var_status.get(), "Parado")
        self.assertEqual(self.app.var_contador.get(), "Cliques: 0")
        self.assertEqual(str(self.app.btn_parar["state"]), "disabled")

    def test_atalhos_aparecem_nos_botoes(self):
        self.assertIn("F6", self.app.btn_iniciar["text"])
        self.assertIn("F7", self.app.btn_capturar["text"])
        self.assertEqual(set(self.app.atalhos.ativos), {"F6", "F7"})

    def test_atalhos_repetidos_sao_recusados(self):
        self.app.var_tecla_capturar.set("F6")
        self.app._aplicar_atalhos()
        self.assertIn("mesma tecla", self.app.var_status.get())

    def test_mostra_os_cliques_por_segundo(self):
        self.app.var_intervalo.set("50")
        self.assertIn("20.0", self.app.var_cps.get())
        self.app.var_intervalo.set("abc")
        self.assertEqual(self.app.var_cps.get(), "")

    # -- campos que ligam e desligam conforme a escolha ------------------

    def test_campos_seguem_o_modo_escolhido(self):
        self.app.var_modo.set(engine.MODE_CLICK)
        self.assertEqual(str(self.app.ent_intervalo["state"]), "normal")
        self.assertEqual(str(self.app.ent_periodico["state"]), "disabled")

        self.app.var_modo.set(engine.MODE_HOLD_CLICK)
        self.assertEqual(str(self.app.ent_intervalo["state"]), "disabled")
        self.assertEqual(str(self.app.ent_periodico["state"]), "normal")

    def test_campos_da_janela_so_ligam_no_modo_segundo_plano(self):
        self.app.var_alvo.set(engine.TARGET_CURSOR)
        self.assertEqual(str(self.app.btn_capturar["state"]), "disabled")
        self.assertEqual(str(self.app.combo_janelas["state"]), "disabled")

        self.app.var_alvo.set(engine.TARGET_WINDOW)
        self.assertEqual(str(self.app.btn_capturar["state"]), "normal")
        self.assertEqual(str(self.app.combo_janelas["state"]), "readonly")

    def test_modo_ponto_da_tela_troca_os_campos(self):
        self.app.var_x.set("10")
        self.app.var_y.set("20")
        self.app.var_alvo.set(engine.TARGET_SCREEN)
        # os campos X e Y passam a mexer nas coordenadas da tela
        self.assertEqual(str(self.app.ent_x["textvariable"]), str(self.app.var_tela_x))
        self.assertEqual(str(self.app.btn_capturar["state"]), "normal")
        self.assertEqual(str(self.app.combo_janelas["state"]), "disabled")
        self.assertEqual(str(self.app.btn_centro["state"]), "disabled")

        self.app.var_alvo.set(engine.TARGET_WINDOW)
        self.assertEqual(str(self.app.ent_x["textvariable"]), str(self.app.var_x))
        self.assertEqual(self.app.var_x.get(), "10", "o ponto da janela foi perdido")

    def test_avisa_que_o_jogo_ignora_clique_em_segundo_plano(self):
        self.app.var_alvo.set(engine.TARGET_WINDOW)
        self.app.hwnd_alvo = 4321
        self.app.processo_alvo = "RobloxPlayerBeta.exe"
        self.assertEqual(self.app._jogo_do_alvo(), "Roblox")
        # askyesno devolve False nos testes: o macro nem chega a começar
        self.app.iniciar()
        self.assertFalse(self.app.motor.running)

    # -- ciclo completo --------------------------------------------------

    def test_inicia_conta_e_para_sozinho_no_limite(self):
        self.app.var_modo.set(engine.MODE_CLICK)
        self.app.var_alvo.set(engine.TARGET_CURSOR)
        self.app.var_intervalo.set("10")
        self.app.var_duracao.set("0")
        self.app.var_limite.set("4")
        self.app.iniciar()

        terminou = self._bombear(ate=lambda: not self.app.motor.running
                                 and "limite" in self.app.var_status.get())
        self.assertTrue(terminou, f"status ficou em: {self.app.var_status.get()}")
        self.assertEqual(self.sender.cliques, 4)
        self.assertEqual(self.app.var_contador.get(), "Cliques: 4")
        self.assertEqual(str(self.app.btn_iniciar["state"]), "normal")
        self.assertEqual(str(self.app.btn_parar["state"]), "disabled")

    def test_o_atalho_liga_e_desliga(self):
        self.app.var_modo.set(engine.MODE_HOLD)
        self.app.var_alvo.set(engine.TARGET_CURSOR)

        self.app.atalhos.ativos["F6"]()          # como se a tecla fosse apertada
        self._bombear(ate=lambda: self.app.motor.running)
        self.assertTrue(self.app.motor.running)
        self.assertEqual(self.sender.cliques, 1)                 # segurou uma vez
        self.assertEqual(str(self.app.btn_iniciar["state"]), "disabled")
        self.assertEqual(str(self.app.btn_parar["state"]), "normal")

        self.app.atalhos.ativos["F6"]()
        parou = self._bombear(ate=lambda: not self.app.motor.running
                              and self.app.var_status.get() == "Parado")
        self.assertTrue(parou, f"status ficou em: {self.app.var_status.get()}")
        self.assertEqual(str(self.app.btn_iniciar["state"]), "normal")
        self.assertEqual(str(self.app.btn_parar["state"]), "disabled")

    def test_avisa_quando_falta_escolher_a_janela(self):
        self.app.var_alvo.set(engine.TARGET_WINDOW)
        self.app.hwnd_alvo = 0
        self.app.iniciar()
        self.assertFalse(self.app.motor.running)
        self.assertTrue(any("janela" in texto.lower() for _, texto in self.alertas),
                        f"nenhum aviso sobre a janela: {self.alertas}")

    def test_avisa_quando_o_numero_esta_errado(self):
        self.app.var_intervalo.set("dez")
        self.app.iniciar()
        self.assertFalse(self.app.motor.running)
        self.assertTrue(any("número" in texto for _, texto in self.alertas),
                        f"nenhum aviso sobre o número: {self.alertas}")

    def test_abre_normalmente_quando_o_icone_existe(self):
        """O .exe traz um icone.ico junto; a janela tem que aceitar isso."""
        from ferramentas import gerar_icone

        raiz = os.path.dirname(os.path.dirname(os.path.abspath(gui.__file__)))
        caminho = os.path.join(raiz, "icone.ico")
        criado = not os.path.exists(caminho)
        if criado:
            gerar_icone.salvar_ico(caminho, (16,))
        try:
            outra = tk.Toplevel(self.root)
            outra.withdraw()
            app = gui.AutoClickerApp(outra)   # não pode levantar exceção
            self.assertEqual(outra.title(), "Auto Clicker")
            app.encerrar()
            outra.destroy()
        finally:
            if criado:
                os.remove(caminho)

    def test_salva_as_preferencias_ao_fechar(self):
        self.app.var_modo.set(engine.MODE_HOLD_CLICK)
        self.app.var_periodico.set("1500")
        self.app.var_tecla_iniciar.set("F8")
        self.app._salvar_configuracao()
        self.assertEqual(self.salvo["mode"], engine.MODE_HOLD_CLICK)
        self.assertEqual(self.salvo["hold_click_every_ms"], 1500)
        self.assertEqual(self.salvo["hotkey_start"], "F8")

    def test_preferencias_invalidas_viram_o_padrao(self):
        self.app.var_limite.set("")
        self.app._salvar_configuracao()
        self.assertEqual(self.salvo["limit"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
