"""Testes do motor de cliques.

O envio real de cliques é trocado por um dublê que apenas anota o que
aconteceu, então os testes rodam em qualquer sistema, sem mexer no mouse.
"""

import os
import sys
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autoclicker import engine  # noqa: E402


class SenderFalso(engine.Sender):
    def __init__(self):
        self.eventos = []
        self.lock = threading.Lock()

    def down(self):
        with self.lock:
            self.eventos.append("down")

    def up(self):
        with self.lock:
            self.eventos.append("up")

    def heartbeat(self):
        with self.lock:
            self.eventos.append("move")

    @property
    def cliques(self):
        with self.lock:
            return self.eventos.count("down")

    @property
    def sem_movimento(self):
        with self.lock:
            return [e for e in self.eventos if e != "move"]


class BaseMotor(unittest.TestCase):
    def setUp(self):
        self.sender = SenderFalso()
        self.original = engine.build_sender
        engine.build_sender = lambda _ajustes: self.sender
        self.contagens = []
        self.fim = threading.Event()
        self.motivo = None
        self.erro = None

        def terminou(motivo, erro):
            self.motivo, self.erro = motivo, erro
            self.fim.set()

        self.motor = engine.ClickEngine(on_count=self.contagens.append, on_finish=terminou)

    def tearDown(self):
        engine.build_sender = self.original
        self.motor.stop()

    def esperar_fim(self, segundos=3.0):
        self.assertTrue(self.fim.wait(segundos), "o motor não terminou a tempo")
        self.assertIsNone(self.erro, f"o motor terminou com erro: {self.erro}")


class TesteAutoClick(BaseMotor):
    def test_clica_repetidamente_ate_mandar_parar(self):
        self.motor.start(engine.ClickSettings(
            mode=engine.MODE_CLICK, interval_ms=20, click_len_ms=0))
        time.sleep(0.45)
        self.motor.stop()
        self.esperar_fim()
        # ~22 cliques em 450 ms; a folga cobre variação de agendamento do SO
        self.assertGreaterEqual(self.sender.cliques, 8)
        self.assertEqual(self.sender.eventos.count("down"), self.sender.eventos.count("up"))
        self.assertEqual(self.motivo, "parado")

    def test_para_sozinho_ao_atingir_o_limite(self):
        self.motor.start(engine.ClickSettings(
            mode=engine.MODE_CLICK, interval_ms=5, click_len_ms=0, limit=7))
        self.esperar_fim()
        self.assertEqual(self.motivo, "limite")
        self.assertEqual(self.sender.cliques, 7)
        self.assertEqual(self.contagens, [1, 2, 3, 4, 5, 6, 7])

    def test_variacao_aleatoria_nao_quebra_o_ritmo(self):
        self.motor.start(engine.ClickSettings(
            mode=engine.MODE_CLICK, interval_ms=20, jitter_pct=50,
            click_len_ms=0, limit=5))
        self.esperar_fim()
        self.assertEqual(self.sender.cliques, 5)


class TesteSegurar(BaseMotor):
    def test_segura_e_solta_apenas_no_fim(self):
        self.motor.start(engine.ClickSettings(mode=engine.MODE_HOLD))
        time.sleep(0.3)
        self.assertEqual(self.sender.sem_movimento, ["down"])  # ainda pressionado
        self.motor.stop()
        self.esperar_fim()
        self.assertEqual(self.sender.sem_movimento, ["down", "up"])

    def test_solta_o_botao_mesmo_se_der_erro(self):
        def explodir():
            raise RuntimeError("janela sumiu")

        self.sender.heartbeat = explodir
        self.motor.start(engine.ClickSettings(mode=engine.MODE_HOLD))
        self.assertTrue(self.fim.wait(3.0))
        self.assertEqual(self.motivo, "erro")
        self.assertIn("janela sumiu", self.erro)
        self.assertEqual(self.sender.sem_movimento[-1], "up")  # não ficou preso


class TesteSegurarComCliquePeriodico(BaseMotor):
    def test_gera_cliques_enquanto_segura(self):
        self.motor.start(engine.ClickSettings(
            mode=engine.MODE_HOLD_CLICK, hold_click_every_ms=60, click_len_ms=10))
        time.sleep(0.5)
        self.motor.stop()
        self.esperar_fim()
        eventos = self.sender.sem_movimento
        self.assertEqual(eventos[0], "down")
        self.assertEqual(eventos[-1], "up")          # nunca termina pressionado
        self.assertGreaterEqual(self.sender.cliques, 3)
        # a sequência é sempre down, up, down, up...
        self.assertEqual(eventos, ["down", "up"] * (len(eventos) // 2))

    def test_respeita_o_limite_de_cliques(self):
        self.motor.start(engine.ClickSettings(
            mode=engine.MODE_HOLD_CLICK, hold_click_every_ms=20,
            click_len_ms=0, limit=3))
        self.esperar_fim()
        self.assertEqual(self.motivo, "limite")
        self.assertEqual(self.sender.cliques, 3)
        self.assertEqual(self.sender.sem_movimento[-1], "up")


class TesteCliqueEmPontoDaTela(unittest.TestCase):
    """O modo que leva o cursor até o ponto, clica e devolve o cursor."""

    def setUp(self):
        self.eventos = []
        self.cursor = (500, 400)
        self.original = (engine.winapi.get_cursor_pos, engine.winapi.set_cursor_pos,
                         engine.winapi.send_physical)

        def mover(x, y):
            self.cursor = (x, y)
            self.eventos.append(("mover", x, y))

        engine.winapi.get_cursor_pos = lambda: self.cursor
        engine.winapi.set_cursor_pos = mover
        engine.winapi.send_physical = lambda botao, apertar: self.eventos.append(
            ("apertar" if apertar else "soltar", botao))

    def tearDown(self):
        (engine.winapi.get_cursor_pos, engine.winapi.set_cursor_pos,
         engine.winapi.send_physical) = self.original

    def test_vai_ate_o_ponto_clica_e_devolve_o_cursor(self):
        enviador = engine.ScreenSender("left", 120, 80)
        enviador.down()
        self.assertEqual(self.cursor, (120, 80))
        self.assertEqual(self.eventos, [("mover", 120, 80), ("apertar", "left")])

        enviador.up()
        self.assertEqual(self.cursor, (500, 400), "o cursor tinha que voltar")
        # solta o botão ANTES de voltar, senão viraria um arrastar
        self.assertEqual(self.eventos[-2:], [("soltar", "left"), ("mover", 500, 400)])

    def test_enquanto_segura_o_cursor_fica_no_ponto(self):
        enviador = engine.ScreenSender("right", 300, 200)
        enviador.down()
        enviador.heartbeat()
        self.assertEqual(self.cursor, (300, 200))
        enviador.up()
        self.assertEqual(self.cursor, (500, 400))

    def test_o_motor_escolhe_esse_modo_e_usa_as_coordenadas_da_tela(self):
        ajustes = engine.ClickSettings(target=engine.TARGET_SCREEN, x=7, y=7,
                                       screen_x=640, screen_y=360)
        ajustes.validate()
        enviador = engine.build_sender(ajustes)
        self.assertIsInstance(enviador, engine.ScreenSender)
        self.assertEqual((enviador.x, enviador.y), (640, 360))


class TesteValidacao(unittest.TestCase):
    def test_recusa_valores_impossiveis(self):
        with self.assertRaises(ValueError):
            engine.ClickSettings(interval_ms=0).validate()
        with self.assertRaises(ValueError):
            engine.ClickSettings(jitter_pct=120).validate()
        with self.assertRaises(ValueError):
            engine.ClickSettings(button="pedal").validate()
        with self.assertRaises(ValueError):
            engine.ClickSettings(limit=-1).validate()

    def test_exige_janela_no_modo_segundo_plano(self):
        with self.assertRaises(ValueError) as caso:
            engine.ClickSettings(target=engine.TARGET_WINDOW, hwnd=0).validate()
        self.assertIn("janela", str(caso.exception).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
