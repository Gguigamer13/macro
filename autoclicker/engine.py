"""Motor de cliques: roda numa thread separada e envia os cliques."""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

from . import winapi

# Modos de clique
MODE_CLICK = "click"            # clica sem parar
MODE_HOLD = "hold"              # segura o botao pressionado
MODE_HOLD_CLICK = "hold_click"  # segura e, de tempos em tempos, da um clique

# Para onde vai o clique
TARGET_CURSOR = "cursor"        # posicao atual do mouse (clique fisico)
TARGET_WINDOW = "window"        # janela escolhida, em segundo plano
TARGET_SCREEN = "screen"        # ponto fixo da tela: leva o cursor, clica e volta

MODE_LABELS = {
    MODE_CLICK: "Auto click",
    MODE_HOLD: "Segurar botao",
    MODE_HOLD_CLICK: "Segurar + clique periodico",
}


@dataclass
class ClickSettings:
    """Tudo que o motor precisa saber para trabalhar."""

    mode: str = MODE_CLICK
    button: str = "left"
    target: str = TARGET_CURSOR
    interval_ms: int = 100          # intervalo entre cliques (modo auto click)
    jitter_pct: int = 0             # variacao aleatoria do intervalo, em %
    hold_click_every_ms: int = 2000  # de quanto em quanto tempo clica segurando
    click_len_ms: int = 30          # quanto tempo o botao fica apertado num clique
    limit: int = 0                  # para depois de N cliques (0 = infinito)
    hwnd: int = 0                   # janela alvo
    x: int = 0                      # ponto do clique, relativo a area cliente
    y: int = 0
    screen_x: int = 0               # ponto do clique em coordenadas da tela
    screen_y: int = 0
    window_title: str = ""

    def validate(self) -> None:
        if self.mode not in MODE_LABELS:
            raise ValueError("Modo de clique invalido.")
        if self.button not in winapi.BUTTONS:
            raise ValueError("Botao do mouse invalido.")
        if self.interval_ms < 1:
            raise ValueError("O intervalo entre cliques precisa ser de pelo menos 1 ms.")
        if self.click_len_ms < 0:
            raise ValueError("A duracao do clique nao pode ser negativa.")
        if self.hold_click_every_ms < 10:
            raise ValueError("O clique periodico precisa ser de pelo menos 10 ms.")
        if not 0 <= self.jitter_pct <= 90:
            raise ValueError("A variacao aleatoria deve ficar entre 0% e 90%.")
        if self.limit < 0:
            raise ValueError("O limite de cliques nao pode ser negativo.")
        if self.target not in (TARGET_CURSOR, TARGET_WINDOW, TARGET_SCREEN):
            raise ValueError("Destino do clique invalido.")
        if self.target == TARGET_WINDOW:
            if not self.hwnd:
                raise ValueError("Escolha uma janela antes de comecar.")
            if not winapi.is_window(self.hwnd):
                raise ValueError("A janela escolhida foi fechada. Selecione outra.")


# --------------------------------------------------------------------------
# Formas de entregar o clique
# --------------------------------------------------------------------------


class Sender:
    """Interface comum entre o clique fisico e o clique em segundo plano."""

    def down(self) -> None: ...
    def up(self) -> None: ...
    def heartbeat(self) -> None:
        """Mensagem opcional enviada enquanto o botao fica segurado."""


class CursorSender(Sender):
    """Clique fisico: acontece onde o cursor estiver naquele instante."""

    def __init__(self, button: str) -> None:
        self.button = button

    def down(self) -> None:
        winapi.send_physical(self.button, True)

    def up(self) -> None:
        winapi.send_physical(self.button, False)


class ScreenSender(Sender):
    """Clique fisico num ponto fixo da tela.

    O cursor vai ate o ponto, clica e volta para onde estava. Serve para jogos
    que so aceitam mouse de verdade (Roblox, Minecraft e companhia), onde o
    clique em segundo plano nao funciona.
    """

    def __init__(self, button: str, x: int, y: int) -> None:
        self.button = button
        self.x = x
        self.y = y
        self._origem: Optional[tuple[int, int]] = None

    def down(self) -> None:
        self._origem = winapi.get_cursor_pos()
        winapi.set_cursor_pos(self.x, self.y)
        winapi.send_physical(self.button, True)

    def up(self) -> None:
        winapi.send_physical(self.button, False)
        if self._origem:  # so volta depois de soltar, senao viraria arrastar
            winapi.set_cursor_pos(*self._origem)
            self._origem = None


class WindowSender(Sender):
    """Clique em segundo plano: a mensagem vai direto para a janela alvo.

    O cursor nao se mexe, entao da para continuar usando o mouse normalmente.
    """

    def __init__(self, button: str, hwnd: int, x: int, y: int) -> None:
        self.button = button
        self.hwnd = hwnd
        self.x = x
        self.y = y
        self._down_msg, self._up_msg, self._mk = (
            winapi.BUTTONS[button][2], winapi.BUTTONS[button][3], winapi.BUTTONS[button][4])
        self._pressed_target: Optional[tuple[int, int, int]] = None

    def _resolve(self) -> tuple[int, int, int]:
        return winapi.resolve_click_target(self.hwnd, self.x, self.y)

    def down(self) -> None:
        target, tx, ty = self._resolve()
        # o movimento antes do clique ajuda apps que so reagem depois de um hover
        winapi.post_mouse_message(target, winapi.WM_MOUSEMOVE, 0, tx, ty)
        winapi.post_mouse_message(target, self._down_msg, self._mk, tx, ty)
        self._pressed_target = (target, tx, ty)

    def up(self) -> None:
        target, tx, ty = self._pressed_target or self._resolve()
        winapi.post_mouse_message(target, self._up_msg, 0, tx, ty)
        self._pressed_target = None

    def heartbeat(self) -> None:
        # enquanto o botao esta segurado, alguns programas esperam receber
        # movimentos do mouse com o botao marcado como pressionado
        if self._pressed_target:
            target, tx, ty = self._pressed_target
            winapi.post_mouse_message(target, winapi.WM_MOUSEMOVE, self._mk, tx, ty)


def build_sender(settings: ClickSettings) -> Sender:
    if settings.target == TARGET_WINDOW:
        return WindowSender(settings.button, settings.hwnd, settings.x, settings.y)
    if settings.target == TARGET_SCREEN:
        return ScreenSender(settings.button, settings.screen_x, settings.screen_y)
    return CursorSender(settings.button)


# --------------------------------------------------------------------------
# Motor
# --------------------------------------------------------------------------


class ClickEngine:
    """Controla a thread que fica clicando."""

    def __init__(self,
                 on_count: Callable[[int], None],
                 on_finish: Callable[[str, Optional[str]], None]) -> None:
        self._on_count = on_count
        self._on_finish = on_finish
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.count = 0

    @property
    def running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def start(self, settings: ClickSettings) -> None:
        if self.running:
            return
        settings.validate()
        self._stop.clear()
        self.count = 0
        thread = threading.Thread(target=self._run, args=(settings,),
                                  name="auto-click", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()

    def stop(self, wait: bool = True) -> None:
        self._stop.set()
        thread = self._thread
        if wait and thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2.0)

    # -- execucao --------------------------------------------------------

    def _wait(self, seconds: float) -> bool:
        """Espera podendo ser interrompida. Retorna False quando mandaram parar."""
        return not self._stop.wait(max(0.0, seconds))

    def _interval(self, settings: ClickSettings) -> float:
        base = settings.interval_ms / 1000.0
        if settings.jitter_pct:
            variation = base * settings.jitter_pct / 100.0
            base = random.uniform(base - variation, base + variation)
        return max(0.0, base)

    def _register_click(self, settings: ClickSettings) -> bool:
        """Conta o clique e diz se ainda pode continuar (por causa do limite)."""
        self.count += 1
        self._on_count(self.count)
        return not (settings.limit and self.count >= settings.limit)

    def _run(self, settings: ClickSettings) -> None:
        reason, error = "parado", None
        high_res = winapi.begin_high_resolution_timer()
        sender = build_sender(settings)
        try:
            if settings.mode == MODE_CLICK:
                reason = self._loop_click(settings, sender)
            elif settings.mode == MODE_HOLD:
                reason = self._loop_hold(settings, sender)
            else:
                reason = self._loop_hold_click(settings, sender)
        except Exception as exc:  # erro de API, janela fechada, etc.
            reason, error = "erro", str(exc)
        finally:
            if high_res:
                winapi.end_high_resolution_timer()
            with self._lock:
                self._thread = None
            self._on_finish(reason, error)

    def _click_once(self, settings: ClickSettings, sender: Sender) -> bool:
        sender.down()
        if settings.click_len_ms:
            if not self._wait(settings.click_len_ms / 1000.0):
                sender.up()
                return False
        sender.up()
        return True

    def _loop_click(self, settings: ClickSettings, sender: Sender) -> str:
        next_at = time.perf_counter()
        while True:
            if not self._click_once(settings, sender):
                return "parado"
            if not self._register_click(settings):
                return "limite"
            next_at += self._interval(settings)
            atraso = next_at - time.perf_counter()
            if atraso < 0:  # nao da para acompanhar o ritmo pedido; reancora
                next_at = time.perf_counter()
                atraso = 0
            if not self._wait(atraso):
                return "parado"

    def _loop_hold(self, settings: ClickSettings, sender: Sender) -> str:
        sender.down()
        self._register_click(settings)
        try:
            while self._wait(0.1):
                sender.heartbeat()
            return "parado"
        finally:
            sender.up()

    def _loop_hold_click(self, settings: ClickSettings, sender: Sender) -> str:
        """Segura o botao e, a cada X ms, solta e aperta de novo (um clique)."""
        sender.down()
        pressed = True
        if not self._register_click(settings):
            sender.up()
            return "limite"
        try:
            periodo = settings.hold_click_every_ms / 1000.0
            gap = max(settings.click_len_ms, 10) / 1000.0
            next_at = time.perf_counter() + periodo
            while True:
                # espera em fatias curtas para manter o heartbeat vivo
                while True:
                    restante = next_at - time.perf_counter()
                    if restante <= 0:
                        break
                    if not self._wait(min(restante, 0.1)):
                        return "parado"
                    sender.heartbeat()
                sender.up()
                pressed = False
                if not self._wait(gap):
                    return "parado"
                sender.down()
                pressed = True
                if not self._register_click(settings):
                    return "limite"
                next_at = time.perf_counter() + periodo
        finally:
            if pressed:
                sender.up()


def single_click(settings: ClickSettings) -> None:
    """Dispara um unico clique - usado pelo botao 'Testar clique'."""
    settings.validate()
    sender = build_sender(settings)
    sender.down()
    time.sleep(max(settings.click_len_ms, 20) / 1000.0)
    sender.up()
