"""Salva e carrega as preferencias do usuario em um arquivo JSON."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

PADRAO: Dict[str, Any] = {
    "mode": "click",
    "button": "left",
    "target": "cursor",
    "interval_ms": 100,
    "jitter_pct": 0,
    "hold_click_every_ms": 2000,
    "click_len_ms": 30,
    "limit": 0,
    "x": 0,
    "y": 0,
    "screen_x": 0,
    "screen_y": 0,
    "hotkey_start": "F6",
    "hotkey_pick": "F7",
    "sempre_visivel": True,
}


def _pasta() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "AutoClickerBR")


def caminho() -> str:
    return os.path.join(_pasta(), "config.json")


def carregar() -> Dict[str, Any]:
    dados = dict(PADRAO)
    try:
        with open(caminho(), "r", encoding="utf-8") as arquivo:
            salvo = json.load(arquivo)
        if isinstance(salvo, dict):
            # so aceita chaves conhecidas, para nao quebrar com arquivo antigo
            dados.update({k: v for k, v in salvo.items() if k in PADRAO})
    except (OSError, ValueError):
        pass
    return dados


def salvar(dados: Dict[str, Any]) -> None:
    try:
        os.makedirs(_pasta(), exist_ok=True)
        with open(caminho(), "w", encoding="utf-8") as arquivo:
            json.dump({k: v for k, v in dados.items() if k in PADRAO},
                      arquivo, indent=2, ensure_ascii=False)
    except OSError:
        pass  # perder a configuracao nao pode derrubar o programa
