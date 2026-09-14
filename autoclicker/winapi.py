"""Ligacoes com a API do Windows (via ctypes) usadas pelo auto clicker.

Nada aqui depende de bibliotecas externas: tudo sai de user32/kernel32/winmm,
que ja existem em qualquer Windows.
"""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    winmm = ctypes.WinDLL("winmm", use_last_error=True)
    try:
        dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
    except OSError:  # pragma: no cover - Windows muito antigo
        dwmapi = None
else:
    user32 = kernel32 = winmm = dwmapi = None


# --------------------------------------------------------------------------
# Constantes
# --------------------------------------------------------------------------

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

INPUT_MOUSE = 0

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208

MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002
MK_MBUTTON = 0x0010

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
MOD_NOREPEAT = 0x4000

GA_ROOT = 2
CWP_SKIPINVISIBLE = 0x0001
CWP_SKIPTRANSPARENT = 0x0004
CWP_SKIPDISABLED = 0x0002

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
DWMWA_CLOAKED = 14

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

SM_CXSCREEN = 0
SM_CYSCREEN = 1

# Codigos virtuais das teclas oferecidas como atalho.
VK_CODES = {f"F{i}": 0x6F + i for i in range(1, 13)}          # F1..F12 -> 0x70..0x7B
VK_CODES.update({"Insert": 0x2D, "Delete": 0x2E, "Home": 0x24, "End": 0x23,
                 "Page Up": 0x21, "Page Down": 0x22, "Scroll Lock": 0x91,
                 "Pause": 0x13, "Num *": 0x6A, "Num -": 0x6D, "Num +": 0x6B})

# Mapa dos botoes do mouse -> (flag down, flag up, msg down, msg up, MK_*)
BUTTONS = {
    "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, WM_LBUTTONDOWN, WM_LBUTTONUP, MK_LBUTTON),
    "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, WM_RBUTTONDOWN, WM_RBUTTONUP, MK_RBUTTON),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP, WM_MBUTTONDOWN, WM_MBUTTONUP, MK_MBUTTON),
}


class WinApiError(RuntimeError):
    """Erro vindo de uma chamada da API do Windows."""


def _require_windows() -> None:
    if not IS_WINDOWS:
        raise WinApiError("Este programa so funciona no Windows.")


# --------------------------------------------------------------------------
# Estruturas
# --------------------------------------------------------------------------


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


if IS_WINDOWS:
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    user32.SendInput.restype = wintypes.UINT
    user32.PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    user32.PostMessageW.restype = wintypes.BOOL
    user32.GetCursorPos.argtypes = (ctypes.POINTER(wintypes.POINT),)
    user32.SetCursorPos.argtypes = (ctypes.c_int, ctypes.c_int)
    user32.GetSystemMetrics.argtypes = (ctypes.c_int,)
    user32.GetSystemMetrics.restype = ctypes.c_int
    user32.WindowFromPoint.argtypes = (wintypes.POINT,)
    user32.WindowFromPoint.restype = wintypes.HWND
    user32.ChildWindowFromPointEx.argtypes = (wintypes.HWND, wintypes.POINT, wintypes.UINT)
    user32.ChildWindowFromPointEx.restype = wintypes.HWND
    user32.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
    user32.GetAncestor.restype = wintypes.HWND
    user32.ScreenToClient.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.POINT))
    user32.ClientToScreen.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.POINT))
    user32.GetClientRect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))
    user32.IsWindow.argtypes = (wintypes.HWND,)
    user32.IsWindowVisible.argtypes = (wintypes.HWND,)
    user32.IsIconic.argtypes = (wintypes.HWND,)
    user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
    user32.GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    user32.EnumWindows.argtypes = (WNDENUMPROC, wintypes.LPARAM)
    user32.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
    user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
    user32.GetMessageW.argtypes = (ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT)
    user32.GetMessageW.restype = ctypes.c_int
    user32.PostThreadMessageW.argtypes = (wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
    user32.FlashWindow.argtypes = (wintypes.HWND, wintypes.BOOL)

    # GetWindowLongPtrW so existe no Windows 64 bits; no 32 bits o nome e GetWindowLongW
    if hasattr(user32, "GetWindowLongPtrW"):
        _get_window_long = user32.GetWindowLongPtrW
        _get_window_long.restype = ctypes.c_ssize_t
    else:
        _get_window_long = user32.GetWindowLongW
        _get_window_long.restype = wintypes.LONG
    _get_window_long.argtypes = (wintypes.HWND, ctypes.c_int)

    dwmapi_ok = dwmapi is not None and hasattr(dwmapi, "DwmGetWindowAttribute")
    if dwmapi_ok:
        dwmapi.DwmGetWindowAttribute.argtypes = (
            wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD)
        dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long

    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = (
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD))
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
else:
    dwmapi_ok = False


# --------------------------------------------------------------------------
# Cliques
# --------------------------------------------------------------------------


def _mouse_event(flag: int) -> None:
    """Envia um evento de mouse fisico na posicao atual do cursor."""
    _require_windows()
    inp = INPUT(type=INPUT_MOUSE)
    inp.mi = MOUSEINPUT(0, 0, 0, flag, 0, 0)
    if user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT)) != 1:
        raise WinApiError(f"SendInput falhou (erro {ctypes.get_last_error()})")


def send_physical(button: str, down: bool) -> None:
    flag_down, flag_up, *_ = BUTTONS[button]
    _mouse_event(flag_down if down else flag_up)


def _make_lparam(x: int, y: int) -> int:
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


def post_mouse_message(hwnd: int, msg: int, wparam: int, x: int, y: int) -> None:
    """Manda uma mensagem de mouse direto para a janela (nao mexe no cursor)."""
    _require_windows()
    if not user32.PostMessageW(hwnd, msg, wparam, _make_lparam(x, y)):
        raise WinApiError(f"PostMessage falhou (erro {ctypes.get_last_error()})")


# --------------------------------------------------------------------------
# Janelas
# --------------------------------------------------------------------------


def is_window(hwnd: int) -> bool:
    return bool(IS_WINDOWS and hwnd and user32.IsWindow(hwnd))


def is_minimized(hwnd: int) -> bool:
    return bool(IS_WINDOWS and hwnd and user32.IsIconic(hwnd))


def get_window_title(hwnd: int) -> str:
    if not IS_WINDOWS:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def get_class_name(hwnd: int) -> str:
    if not IS_WINDOWS:
        return ""
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def get_process_name(hwnd: int) -> str:
    """Nome do executavel dono da janela (ex.: chrome.exe). Vazio se nao der."""
    if not IS_WINDOWS:
        return ""
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(512)
        buf = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value)
        return ""
    finally:
        kernel32.CloseHandle(handle)


def _is_cloaked(hwnd: int) -> bool:
    """Janelas UWP 'fantasma' ficam cloaked; nao interessa listar elas."""
    if not dwmapi_ok:
        return False
    cloaked = wintypes.DWORD()
    result = dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(hwnd), wintypes.DWORD(DWMWA_CLOAKED),
        ctypes.byref(cloaked), ctypes.sizeof(cloaked))
    return result == 0 and cloaked.value != 0


def list_windows() -> list[dict]:
    """Lista as janelas abertas (visiveis, com titulo) para o usuario escolher."""
    _require_windows()
    found: list[dict] = []

    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        title = get_window_title(hwnd)
        if not title:
            return True
        if _get_window_long(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW:
            return True
        if _is_cloaked(hwnd):
            return True
        found.append({"hwnd": int(hwnd), "title": title, "process": get_process_name(hwnd)})
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    found.sort(key=lambda w: (w["process"].lower(), w["title"].lower()))
    return found


def get_cursor_pos() -> tuple[int, int]:
    _require_windows()
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def set_cursor_pos(x: int, y: int) -> None:
    """Leva o cursor para um ponto da tela."""
    _require_windows()
    if not user32.SetCursorPos(int(x), int(y)):
        raise WinApiError(f"Nao consegui mover o cursor (erro {ctypes.get_last_error()})")


def get_screen_size() -> tuple[int, int]:
    """Tamanho da tela principal, em pixels."""
    _require_windows()
    return user32.GetSystemMetrics(SM_CXSCREEN), user32.GetSystemMetrics(SM_CYSCREEN)


def get_client_size(hwnd: int) -> tuple[int, int]:
    _require_windows()
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    return rect.right - rect.left, rect.bottom - rect.top


def screen_to_client(hwnd: int, x: int, y: int) -> tuple[int, int]:
    _require_windows()
    pt = wintypes.POINT(x, y)
    user32.ScreenToClient(hwnd, ctypes.byref(pt))
    return pt.x, pt.y


def client_to_screen(hwnd: int, x: int, y: int) -> tuple[int, int]:
    _require_windows()
    pt = wintypes.POINT(x, y)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y


def window_at_cursor() -> tuple[int, int, int]:
    """Janela principal sob o cursor + coordenadas do ponto na area cliente dela.

    Retorna (hwnd_da_janela_principal, x, y).
    """
    _require_windows()
    sx, sy = get_cursor_pos()
    child = user32.WindowFromPoint(wintypes.POINT(sx, sy))
    if not child:
        raise WinApiError("Nenhuma janela debaixo do cursor.")
    root = user32.GetAncestor(child, GA_ROOT) or child
    cx, cy = screen_to_client(root, sx, sy)
    return int(root), cx, cy


def resolve_click_target(hwnd: int, x: int, y: int) -> tuple[int, int, int]:
    """Desce ate o controle filho que fica embaixo do ponto (x, y).

    (x, y) sao coordenadas da area cliente da janela principal. Muitos programas
    (navegadores, jogos) so respondem se a mensagem chegar no filho certo, e nao
    na janela de fora. Percorremos a arvore sem usar WindowFromPoint, que so
    enxerga quem esta na frente na tela - aqui a janela pode estar atras.
    """
    _require_windows()
    if not is_window(hwnd):
        raise WinApiError("A janela escolhida nao existe mais.")

    target = hwnd
    tx, ty = x, y
    for _ in range(16):  # profundidade de sobra; evita loop infinito
        pt = wintypes.POINT(tx, ty)
        child = user32.ChildWindowFromPointEx(
            target, pt, CWP_SKIPINVISIBLE | CWP_SKIPTRANSPARENT)
        if not child or int(child) == int(target):
            break
        # converte o ponto para a area cliente do filho
        sx, sy = client_to_screen(target, tx, ty)
        tx, ty = screen_to_client(child, sx, sy)
        target = int(child)
    return int(target), tx, ty


# --------------------------------------------------------------------------
# Precisao do timer (sem isso o sleep do Windows erra ate 15 ms)
# --------------------------------------------------------------------------


def begin_high_resolution_timer() -> bool:
    if not IS_WINDOWS:
        return False
    return winmm.timeBeginPeriod(1) == 0


def end_high_resolution_timer() -> None:
    if IS_WINDOWS:
        winmm.timeEndPeriod(1)
