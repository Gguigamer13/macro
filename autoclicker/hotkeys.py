"""Atalhos globais (funcionam mesmo com outro programa em primeiro plano)."""

from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Callable, Dict, Optional

from . import winapi

WM_STOP_LISTENER = 0x0400 + 1  # WM_USER + 1


class HotkeyListener:
    """Registra atalhos globais numa thread com fila de mensagens propria.

    O Windows exige que RegisterHotKey e o laco de mensagens fiquem na mesma
    thread, entao cada troca de atalho recria a thread - e barato e simples.
    """

    def __init__(self, on_error: Optional[Callable[[str], None]] = None) -> None:
        self._on_error = on_error
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._ready = threading.Event()

    def set_hotkeys(self, hotkeys: Dict[str, Callable[[], None]]) -> None:
        """Define os atalhos ativos. Chave = nome da tecla (ex.: "F6")."""
        self.stop()
        if not winapi.IS_WINDOWS or not hotkeys:
            return
        self._ready.clear()
        self._thread = threading.Thread(target=self._run, args=(dict(hotkeys),),
                                        name="hotkeys", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=2.0)

    def stop(self) -> None:
        if self._thread and self._thread.is_alive() and self._thread_id:
            winapi.user32.PostThreadMessageW(self._thread_id, WM_STOP_LISTENER, 0, 0)
            self._thread.join(timeout=2.0)
        self._thread = None
        self._thread_id = None

    # -- thread ----------------------------------------------------------

    def _run(self, hotkeys: Dict[str, Callable[[], None]]) -> None:
        user32 = winapi.user32
        self._thread_id = winapi.kernel32.GetCurrentThreadId()
        acoes: Dict[int, Callable[[], None]] = {}
        registrados: list[int] = []
        falhas: list[str] = []

        for indice, (tecla, acao) in enumerate(hotkeys.items(), start=1):
            vk = winapi.VK_CODES.get(tecla)
            if vk is None:
                falhas.append(tecla)
                continue
            if user32.RegisterHotKey(None, indice, winapi.MOD_NOREPEAT, vk):
                acoes[indice] = acao
                registrados.append(indice)
            else:
                falhas.append(tecla)

        self._ready.set()
        if falhas and self._on_error:
            self._on_error("Nao consegui registrar: " + ", ".join(falhas)
                           + " (outro programa ja usa essa tecla). Escolha outra.")

        try:
            msg = wintypes.MSG()
            while True:
                resultado = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if resultado in (0, -1):  # WM_QUIT ou erro
                    break
                if msg.message == WM_STOP_LISTENER:
                    break
                if msg.message == winapi.WM_HOTKEY:
                    acao = acoes.get(int(msg.wParam))
                    if acao:
                        try:
                            acao()
                        except Exception as exc:  # nunca deixa a thread morrer
                            if self._on_error:
                                self._on_error(f"Erro no atalho: {exc}")
        finally:
            for indice in registrados:
                user32.UnregisterHotKey(None, indice)
