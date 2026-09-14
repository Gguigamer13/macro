"""Paleta, estilos e elementos gráficos do Auto Clicker.

Tudo é desenhado com o próprio tkinter (Canvas), sem imagens externas: assim o
programa continua sendo só uma pasta com arquivos .py.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import Optional

# Paleta: branco gelo + azul bebê
CORES = {
    "gelo": "#EDF4FA",        # fundo geral
    "cartao": "#FBFDFF",      # fundo dos cartões
    "azul_bebe": "#A9D6F2",   # azul bebê principal
    "azul_claro": "#D8ECFA",  # azul bebê claro
    "azul_medio": "#7CBCE4",
    "azul_escuro": "#2F6A96",  # títulos
    "texto": "#2C4356",
    "texto_suave": "#6E8CA4",
    "borda": "#D3E4F1",
    "verde": "#3C9A6B",
    "vermelho": "#C25B57",
    "ambar": "#C08A2B",
    "marca": "#B4CFE3",       # marca d'água
}


def _rgb(cor: str) -> tuple[int, int, int]:
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def mistura(cor1: str, cor2: str, quanto: float) -> str:
    """Cor intermediária entre duas cores (quanto = 0.0 a 1.0)."""
    a, b = _rgb(cor1), _rgb(cor2)
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, round(a[i] + (b[i] - a[i]) * quanto))) for i in range(3))


def escolher_fonte(root: tk.Misc) -> str:
    disponiveis = set(tkfont.families(root))
    for nome in ("Segoe UI", "Calibri", "DejaVu Sans", "Helvetica", "Arial"):
        if nome in disponiveis:
            return nome
    return "TkDefaultFont"


def aplicar_estilos(root: tk.Misc) -> dict:
    """Configura os widgets ttk e devolve as fontes usadas na interface."""
    fonte = escolher_fonte(root)
    fontes = {
        "titulo": (fonte, 17, "bold"),
        "subtitulo": (fonte, 9),
        "cartao": (fonte, 10, "bold"),
        "normal": (fonte, 9),
        "forte": (fonte, 9, "bold"),
        "pequena": (fonte, 8),
        "botao": (fonte, 10, "bold"),
        "familia": fonte,
    }

    estilo = ttk.Style(root)
    if "clam" in estilo.theme_names():  # o único tema que aceita cor em tudo
        estilo.theme_use("clam")

    estilo.configure("Gelo.TNotebook", background=CORES["gelo"], borderwidth=0,
                     tabmargins=(10, 8, 10, 0))
    estilo.configure("Gelo.TNotebook.Tab", background=CORES["azul_claro"],
                     foreground=CORES["azul_escuro"], borderwidth=0,
                     padding=(18, 9), font=(fonte, 10, "bold"))
    estilo.map("Gelo.TNotebook.Tab",
               background=[("selected", CORES["cartao"]), ("active", CORES["azul_bebe"])],
               foreground=[("selected", CORES["azul_escuro"])],
               expand=[("selected", (0, 0, 0, 2))])

    estilo.configure("Gelo.TCombobox", padding=5,
                     fieldbackground=CORES["cartao"], background=CORES["azul_claro"],
                     foreground=CORES["texto"], arrowcolor=CORES["azul_escuro"],
                     bordercolor=CORES["borda"], lightcolor=CORES["borda"],
                     darkcolor=CORES["borda"], selectbackground=CORES["azul_claro"],
                     selectforeground=CORES["texto"])
    estilo.map("Gelo.TCombobox",
               fieldbackground=[("disabled", CORES["gelo"]), ("readonly", CORES["cartao"])],
               foreground=[("disabled", CORES["texto_suave"])],
               bordercolor=[("focus", CORES["azul_medio"])],
               arrowcolor=[("disabled", CORES["borda"])])

    # cores da listinha que abre no combobox
    root.option_add("*TCombobox*Listbox.background", CORES["cartao"])
    root.option_add("*TCombobox*Listbox.foreground", CORES["texto"])
    root.option_add("*TCombobox*Listbox.selectBackground", CORES["azul_bebe"])
    root.option_add("*TCombobox*Listbox.selectForeground", CORES["azul_escuro"])
    root.option_add("*TCombobox*Listbox.font", (fonte, 9))
    return fontes


# --------------------------------------------------------------------------
# Ícones desenhados (todos cabem numa caixa de 22x22)
# --------------------------------------------------------------------------


def icone_mouse(tela: tk.Canvas, x: int, y: int, cor: str, escala: float = 1.0,
                cheio: bool = False, tag: str = "") -> None:
    """Desenho de um mouse; 'cheio' pinta o botão esquerdo (modo segurar)."""
    e = escala
    corpo = (x - 7 * e, y - 10 * e, x + 7 * e, y + 10 * e)
    tela.create_oval(*corpo, outline=cor, width=max(1, 1.6 * e),
                     fill=CORES["cartao"] if not cheio else CORES["azul_claro"], tags=tag)
    if cheio:
        tela.create_arc(*corpo, start=90, extent=90, outline=cor, fill=cor,
                        width=1, style="pieslice", tags=tag)
    tela.create_line(x, y - 10 * e, x, y - 1 * e, fill=cor, width=max(1, 1.4 * e), tags=tag)
    tela.create_line(x - 7 * e, y - 1 * e, x + 7 * e, y - 1 * e, fill=cor,
                     width=max(1, 1.4 * e), tags=tag)


def icone_relogio(tela: tk.Canvas, x: int, y: int, cor: str, tag: str = "") -> None:
    tela.create_oval(x - 9, y - 9, x + 9, y + 9, outline=cor, width=1.6,
                     fill=CORES["cartao"], tags=tag)
    tela.create_line(x, y, x, y - 5, fill=cor, width=1.6, tags=tag)
    tela.create_line(x, y, x + 4, y + 2, fill=cor, width=1.6, tags=tag)


def icone_alvo(tela: tk.Canvas, x: int, y: int, cor: str, tag: str = "") -> None:
    tela.create_oval(x - 9, y - 9, x + 9, y + 9, outline=cor, width=1.6, tags=tag)
    tela.create_oval(x - 4, y - 4, x + 4, y + 4, outline=cor, width=1.4, tags=tag)
    tela.create_oval(x - 1, y - 1, x + 1, y + 1, fill=cor, outline=cor, tags=tag)
    for dx, dy in ((-12, 0), (12, 0), (0, -12), (0, 12)):
        tela.create_line(x + dx * 0.75, y + dy * 0.75, x + dx, y + dy,
                         fill=cor, width=1.4, tags=tag)


def icone_janela(tela: tk.Canvas, x: int, y: int, cor: str, tag: str = "") -> None:
    tela.create_rectangle(x - 10, y - 8, x + 10, y + 8, outline=cor, width=1.6,
                          fill=CORES["cartao"], tags=tag)
    tela.create_rectangle(x - 10, y - 8, x + 10, y - 3, outline=cor, width=1.4,
                          fill=CORES["azul_claro"], tags=tag)
    tela.create_oval(x + 3, y + 1, x + 7, y + 5, outline=cor, fill=cor, tags=tag)


def icone_cursor(tela: tk.Canvas, x: int, y: int, cor: str, tag: str = "") -> None:
    tela.create_polygon(x - 5, y - 9, x - 5, y + 7, x - 1, y + 3, x + 2, y + 9,
                        x + 5, y + 7, x + 2, y + 1, x + 7, y + 1,
                        outline=cor, fill=CORES["cartao"], width=1.4, tags=tag)


def icone_teclado(tela: tk.Canvas, x: int, y: int, cor: str, tag: str = "") -> None:
    tela.create_rectangle(x - 11, y - 7, x + 11, y + 7, outline=cor, width=1.6,
                          fill=CORES["cartao"], tags=tag)
    for dx in (-7, -2, 3):
        tela.create_line(x + dx, y - 3, x + dx + 2, y - 3, fill=cor, width=1.6, tags=tag)
    for dx in (-8, -3, 2, 7):
        tela.create_line(x + dx, y + 1, x + dx + 2, y + 1, fill=cor, width=1.6, tags=tag)
    tela.create_line(x - 5, y + 5, x + 5, y + 5, fill=cor, width=1.6, tags=tag)


def icone_repetir(tela: tk.Canvas, x: int, y: int, cor: str, tag: str = "") -> None:
    tela.create_arc(x - 9, y - 9, x + 9, y + 9, start=40, extent=280, style="arc",
                    outline=cor, width=1.8, tags=tag)
    tela.create_polygon(x + 6, y - 9, x + 11, y - 4, x + 4, y - 2,
                        fill=cor, outline=cor, tags=tag)


ICONES = {
    "mouse": icone_mouse, "relogio": icone_relogio, "alvo": icone_alvo,
    "janela": icone_janela, "cursor": icone_cursor, "teclado": icone_teclado,
    "repetir": icone_repetir,
}


# --------------------------------------------------------------------------
# Peças da interface
# --------------------------------------------------------------------------


class Cartao(tk.Frame):
    """Caixa branca com borda suave, título e ícone."""

    def __init__(self, pai: tk.Misc, fontes: dict, titulo: str = "",
                 icone: str = "", **kwargs) -> None:
        super().__init__(pai, bg=CORES["cartao"], highlightthickness=1,
                         highlightbackground=CORES["borda"], bd=0, **kwargs)
        if titulo:
            topo = tk.Frame(self, bg=CORES["cartao"])
            topo.pack(fill="x", padx=12, pady=(10, 0))
            if icone:
                marca = tk.Canvas(topo, width=24, height=24, bg=CORES["cartao"],
                                  highlightthickness=0)
                ICONES[icone](marca, 12, 12, CORES["azul_escuro"])
                marca.pack(side="left", padx=(0, 8))
            tk.Label(topo, text=titulo, font=fontes["cartao"], bg=CORES["cartao"],
                     fg=CORES["azul_escuro"]).pack(side="left")
            risco = tk.Frame(self, bg=CORES["azul_claro"], height=2)
            risco.pack(fill="x", padx=12, pady=(6, 0))
        self.corpo = tk.Frame(self, bg=CORES["cartao"])
        self.corpo.pack(fill="both", expand=True, padx=12, pady=10)


class Cabecalho(tk.Canvas):
    """Faixa de cima: degradê azul bebê, logo do mouse e ondas de clique."""

    ALTURA = 92

    def __init__(self, pai: tk.Misc, fontes: dict) -> None:
        super().__init__(pai, height=self.ALTURA, bg=CORES["azul_claro"],
                         highlightthickness=0)
        self.fontes = fontes
        self._animando = False
        self._fase = 0.0
        self._agendado = None
        self.bind("<Configure>", lambda _e: self._desenhar())
        self.bind("<Destroy>", lambda _e: self.parar_animacao())

    def _desenhar(self) -> None:
        largura = max(self.winfo_width(), 1)
        self.delete("all")
        # degradê horizontal do azul bebê para o branco gelo
        passos = 60
        for i in range(passos):
            cor = mistura(CORES["azul_bebe"], CORES["gelo"], i / (passos - 1))
            x0 = largura * i / passos
            self.create_rectangle(x0, 0, largura * (i + 1) / passos + 1, self.ALTURA,
                                  fill=cor, outline=cor)
        # bolhas decorativas
        for cx, cy, r, t in ((largura - 60, 20, 46, 0.55), (largura - 130, 74, 30, 0.7),
                             (largura - 20, 78, 22, 0.45)):
            cor = mistura(CORES["azul_bebe"], CORES["cartao"], t)
            self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=cor, width=2)
        self.create_line(0, self.ALTURA - 1, largura, self.ALTURA - 1,
                         fill=CORES["azul_medio"])
        # logo
        self.create_oval(22, 22, 70, 70, fill=CORES["cartao"], outline=CORES["azul_medio"],
                         width=2)
        icone_mouse(self, 46, 46, CORES["azul_escuro"], escala=1.25)
        self.create_text(88, 36, text="AUTO CLICKER", anchor="w",
                         font=self.fontes["titulo"], fill=CORES["azul_escuro"])
        self.create_text(89, 58, text="clique automático · segurar · clique em segundo plano",
                         anchor="w", font=self.fontes["subtitulo"], fill=CORES["texto_suave"])
        self._desenhar_ondas()

    def _desenhar_ondas(self) -> None:
        self.delete("onda")
        if not self._animando:
            return
        for indice in range(3):
            avanco = (self._fase + indice / 3.0) % 1.0
            raio = 22 + avanco * 18
            cor = mistura(CORES["azul_medio"], CORES["gelo"], min(1.0, avanco))
            self.create_oval(46 - raio, 46 - raio, 46 + raio, 46 + raio,
                             outline=cor, width=2, tags="onda")

    def animar(self, ligado: bool) -> None:
        if ligado == self._animando:
            return
        self._animando = ligado
        if ligado:
            self._passo()
        else:
            self.parar_animacao()
            self._desenhar_ondas()

    def _passo(self) -> None:
        if not self._animando or not self.winfo_exists():
            return
        self._fase = (self._fase + 0.035) % 1.0
        self._desenhar_ondas()
        self._agendado = self.after(45, self._passo)

    def parar_animacao(self) -> None:
        self._animando = False
        if self._agendado is not None:
            try:
                self.after_cancel(self._agendado)
            except tk.TclError:
                pass
            self._agendado = None


class Indicador(tk.Canvas):
    """Luzinha de status ao lado do texto 'Parado / rodando'."""

    def __init__(self, pai: tk.Misc, fundo: str) -> None:
        super().__init__(pai, width=22, height=22, bg=fundo, highlightthickness=0)
        self.cor = CORES["texto_suave"]
        self.desenhar()

    def definir(self, cor: str) -> None:
        self.cor = cor
        self.desenhar()

    def desenhar(self) -> None:
        self.delete("all")
        halo = mistura(self.cor, self["bg"], 0.72)
        self.create_oval(2, 2, 20, 20, outline=halo, fill=halo)
        self.create_oval(6, 6, 16, 16, outline=self.cor, fill=self.cor)


class MarcaDagua(tk.Canvas):
    """Marca d'água do rodapé: powered by nova era."""

    ALTURA = 34

    def __init__(self, pai: tk.Misc, fontes: dict) -> None:
        super().__init__(pai, height=self.ALTURA, bg=CORES["gelo"], highlightthickness=0)
        self.fontes = fontes
        self._f1 = tkfont.Font(family=fontes["familia"], size=8)
        self._f2 = tkfont.Font(family=fontes["familia"], size=9, weight="bold")
        self.bind("<Configure>", lambda _e: self._desenhar())

    def _desenhar(self) -> None:
        largura = max(self.winfo_width(), 1)
        meio = self.ALTURA // 2
        self.delete("all")
        texto1, texto2 = "powered by", "nova era"
        bloco = 24 + self._f1.measure(texto1) + 6 + self._f2.measure(texto2)
        x = (largura - bloco) / 2
        # linhas finas dos dois lados
        self.create_line(18, meio, x - 12, meio, fill=CORES["borda"])
        self.create_line(x + bloco + 12, meio, largura - 18, meio, fill=CORES["borda"])
        # emblema
        self.create_oval(x, meio - 9, x + 18, meio + 9, outline=CORES["marca"], width=1.4)
        self.create_text(x + 9, meio, text="NE", font=(self.fontes["familia"], 7, "bold"),
                         fill=CORES["marca"])
        self.create_text(x + 24, meio, text=texto1, anchor="w", font=self._f1,
                         fill=CORES["marca"])
        self.create_text(x + 24 + self._f1.measure(texto1) + 6, meio, text=texto2,
                         anchor="w", font=self._f2, fill=CORES["marca"])


class MapaAlvo(tk.Canvas):
    """Mini mapa da janela alvo mostrando onde o clique vai cair."""

    ALTURA = 168

    def __init__(self, pai: tk.Misc, fontes: dict) -> None:
        super().__init__(pai, height=self.ALTURA, bg=CORES["cartao"], highlightthickness=0)
        self.fontes = fontes
        self._dados = None
        self.bind("<Configure>", lambda _e: self.redesenhar())

    def mostrar(self, largura: int, altura: int, x: int, y: int, titulo: str) -> None:
        self._dados = (largura, altura, x, y, titulo)
        self.redesenhar()

    def limpar(self, mensagem: str) -> None:
        self._dados = mensagem
        self.redesenhar()

    def redesenhar(self) -> None:
        self.delete("all")
        largura_tela = max(self.winfo_width(), 1)
        if not isinstance(self._dados, tuple):
            self.create_text(largura_tela / 2, self.ALTURA / 2,
                             text=self._dados or "Nenhuma janela selecionada.",
                             font=self.fontes["normal"], fill=CORES["texto_suave"])
            return

        larg, alt, px, py, titulo = self._dados
        if larg <= 0 or alt <= 0:
            larg, alt = 16, 9
        # caixa proporcional à janela alvo, centralizada
        max_l, max_a = largura_tela - 60, self.ALTURA - 36
        escala = min(max_l / larg, max_a / alt)
        cl, ca = larg * escala, alt * escala
        x0, y0 = (largura_tela - cl) / 2, (self.ALTURA - ca) / 2 + 4

        self.create_rectangle(x0 + 3, y0 + 3, x0 + cl + 3, y0 + ca + 3,
                              fill=CORES["gelo"], outline=CORES["gelo"])  # sombrinha
        self.create_rectangle(x0, y0, x0 + cl, y0 + ca, fill=CORES["azul_claro"],
                              outline=CORES["azul_medio"])
        self.create_rectangle(x0, y0, x0 + cl, y0 + 12, fill=CORES["azul_bebe"],
                              outline=CORES["azul_medio"])
        nome = titulo if len(titulo) <= 34 else titulo[:31] + "..."
        self.create_text(x0 + 6, y0 + 6, text=nome, anchor="w",
                         font=self.fontes["pequena"], fill=CORES["azul_escuro"])

        # marcador do ponto do clique
        mx = x0 + max(0.0, min(1.0, px / larg)) * cl
        my = y0 + max(0.0, min(1.0, py / alt)) * ca
        self.create_line(x0, my, x0 + cl, my, fill=CORES["azul_medio"], dash=(3, 3))
        self.create_line(mx, y0, mx, y0 + ca, fill=CORES["azul_medio"], dash=(3, 3))
        for raio, cor in ((9, CORES["azul_medio"]), (5, CORES["azul_escuro"])):
            self.create_oval(mx - raio, my - raio, mx + raio, my + raio, outline=cor, width=1.6)
        self.create_oval(mx - 2, my - 2, mx + 2, my + 2,
                         fill=CORES["azul_escuro"], outline=CORES["azul_escuro"])
        self.create_text(largura_tela / 2, self.ALTURA - 8,
                         text=f"clique em X {px} · Y {py}   (janela de {larg}x{alt})",
                         font=self.fontes["pequena"], fill=CORES["texto_suave"])


class Botao(tk.Button):
    """Botão chapado, com cor de destaque e efeito ao passar o mouse."""

    def __init__(self, pai: tk.Misc, fontes: dict, texto: str, comando,
                 principal: bool = False, **kwargs) -> None:
        self._fundo = CORES["azul_bebe"] if principal else CORES["cartao"]
        self._hover = CORES["azul_medio"] if principal else CORES["azul_claro"]
        super().__init__(pai, text=texto, command=comando, font=fontes["botao"] if principal
                         else fontes["normal"], bg=self._fundo, fg=CORES["azul_escuro"],
                         activebackground=self._hover, activeforeground=CORES["azul_escuro"],
                         disabledforeground=CORES["texto_suave"], relief="flat", bd=0,
                         highlightthickness=1, highlightbackground=CORES["borda"],
                         cursor="hand2", **kwargs)
        self.bind("<Enter>", self._entrou)
        self.bind("<Leave>", self._saiu)

    def _entrou(self, _evento=None) -> None:
        if str(self["state"]) != "disabled":
            self.configure(bg=self._hover)

    def _saiu(self, _evento=None) -> None:
        self.configure(bg=self._fundo)


def rotulo(pai: tk.Misc, texto: str, fontes: dict, tipo: str = "normal",
           fundo: str = CORES["cartao"], **kwargs) -> tk.Label:
    cores = {"normal": CORES["texto"], "suave": CORES["texto_suave"],
             "forte": CORES["azul_escuro"]}
    fonte = fontes["forte"] if tipo == "forte" else fontes[
        "pequena" if tipo == "suave" else "normal"]
    return tk.Label(pai, text=texto, font=fonte, bg=fundo,
                    fg=cores.get(tipo, CORES["texto"]), **kwargs)


def entrada(pai: tk.Misc, variavel: tk.StringVar, fontes: dict, largura: int = 8) -> tk.Entry:
    return tk.Entry(pai, textvariable=variavel, width=largura, font=fontes["normal"],
                    bg=CORES["cartao"], fg=CORES["texto"], relief="flat",
                    highlightthickness=1, highlightbackground=CORES["borda"],
                    highlightcolor=CORES["azul_medio"], insertbackground=CORES["texto"],
                    disabledbackground=CORES["gelo"], disabledforeground=CORES["texto_suave"],
                    justify="center")


def radio(pai: tk.Misc, texto: str, variavel: tk.StringVar, valor: str, fontes: dict,
          fundo: str = CORES["cartao"], comando=None) -> tk.Radiobutton:
    return tk.Radiobutton(pai, text=texto, variable=variavel, value=valor,
                          font=fontes["forte"], bg=fundo, fg=CORES["texto"],
                          activebackground=fundo, activeforeground=CORES["azul_escuro"],
                          selectcolor=CORES["cartao"], relief="flat", bd=0,
                          highlightthickness=0, anchor="w", cursor="hand2",
                          command=comando)


class Dica(tk.Frame):
    """Faixa azul clara com um aviso útil no pé da aba."""

    def __init__(self, pai: tk.Misc, fontes: dict, texto: str, icone: str = "alvo") -> None:
        super().__init__(pai, bg=CORES["azul_claro"], highlightthickness=1,
                         highlightbackground=CORES["borda"], bd=0)
        desenho = tk.Canvas(self, width=26, height=26, bg=CORES["azul_claro"],
                            highlightthickness=0)
        ICONES[icone](desenho, 13, 13, CORES["azul_escuro"])
        desenho.pack(side="left", padx=(10, 6), pady=8)
        tk.Label(self, text=texto, font=fontes["pequena"], bg=CORES["azul_claro"],
                 fg=CORES["azul_escuro"], justify="left", anchor="w",
                 wraplength=520).pack(side="left", fill="x", expand=True,
                                      padx=(0, 10), pady=8)


class Diagrama(tk.Canvas):
    """Desenho comparando o clique no cursor e o clique em segundo plano."""

    ALTURA = 132

    def __init__(self, pai: tk.Misc, fontes: dict) -> None:
        super().__init__(pai, height=self.ALTURA, bg=CORES["cartao"],
                         highlightthickness=0)
        self.fontes = fontes
        self._destaque = ""
        self.bind("<Configure>", lambda _e: self.redesenhar())

    def mostrar(self, destino: str) -> None:
        self._destaque = destino
        self.redesenhar()

    def redesenhar(self) -> None:
        self.delete("all")
        largura = max(self.winfo_width(), 2)
        meio = largura / 2
        self.create_line(meio, 12, meio, self.ALTURA - 12, fill=CORES["borda"])
        self._cena(meio / 2, self._destaque == "cursor", True)
        self._cena(meio + meio / 2, self._destaque == "window", False)

    def _cena(self, centro: float, ativa: bool, no_cursor: bool) -> None:
        """Uma das duas cenas; a inativa fica desbotada."""
        def cor(nome: str) -> str:
            base = CORES[nome]
            return base if ativa else mistura(base, CORES["cartao"], 0.62)

        x0, y0, x1, y1 = centro - 62, 14, centro + 26, 78
        self.create_rectangle(x0, y0, x1, y1, outline=cor("azul_medio"),
                              fill=cor("azul_claro") if ativa else CORES["cartao"])
        self.create_rectangle(x0, y0, x1, y0 + 10, outline=cor("azul_medio"),
                              fill=cor("azul_bebe"))
        for i in range(3):
            self.create_line(x0 + 6, y0 + 20 + i * 11, x1 - 10, y0 + 20 + i * 11,
                             fill=cor("borda"))

        # ponto que recebe o clique, com as ondas
        px, py = centro - 12, y1 - 16
        for raio in (6, 11, 16):
            self.create_oval(px - raio, py - raio, px + raio, py + raio,
                             outline=cor("azul_medio" if raio < 16 else "borda"))
        self.create_oval(px - 3, py - 3, px + 3, py + 3,
                         fill=cor("azul_escuro"), outline=cor("azul_escuro"))

        # o cursor: dentro da janela num caso, longe e livre no outro
        if no_cursor:
            icone_cursor(self, px + 10, py + 8, cor("azul_escuro"))
            legenda = "o clique cai onde o\ncursor estiver"
        else:
            cx, cy = centro + 46, 34
            icone_cursor(self, cx, cy, cor("azul_escuro"))
            self.create_text(cx + 4, cy + 18, text="livre", anchor="n",
                             font=self.fontes["pequena"], fill=cor("verde"))
            self.create_line(cx - 12, cy + 6, px + 18, py - 14, fill=cor("borda"),
                             dash=(3, 3))
            legenda = "a janela recebe o clique\ne o mouse continua livre"
        self.create_text(centro, self.ALTURA - 26, text=legenda, justify="center",
                         font=self.fontes["pequena"],
                         fill=cor("azul_escuro") if ativa else CORES["texto_suave"])


class Velocimetro(tk.Canvas):
    """Barra que mostra visualmente o ritmo escolhido, de lento a muito rápido."""

    ALTURA = 50
    MARCAS = [(1, "1"), (2, "2"), (5, "5"), (10, "10"), (20, "20"), (50, "50"),
              (100, "100")]
    MIN, MAX = 0.5, 200.0

    def __init__(self, pai: tk.Misc, fontes: dict) -> None:
        super().__init__(pai, height=self.ALTURA, bg=CORES["cartao"],
                         highlightthickness=0)
        self.fontes = fontes
        self._cps: Optional[float] = None
        self.bind("<Configure>", lambda _e: self.redesenhar())

    def definir(self, cps: Optional[float]) -> None:
        self._cps = cps
        self.redesenhar()

    def _posicao(self, largura: float, cps: float) -> float:
        """Escala logarítmica: 1, 10 e 100 ficam bem espaçados na barra."""
        import math
        cps = max(self.MIN, min(self.MAX, cps))
        fatia = (math.log10(cps) - math.log10(self.MIN)) / (
            math.log10(self.MAX) - math.log10(self.MIN))
        return 16 + fatia * (largura - 32)

    def redesenhar(self) -> None:
        self.delete("all")
        largura = max(self.winfo_width(), 2)
        topo, base = 20, 32
        passos = 48
        for i in range(passos):
            cor = mistura(CORES["azul_claro"], CORES["azul_escuro"], i / (passos - 1))
            x0 = 16 + (largura - 32) * i / passos
            self.create_rectangle(x0, topo, x0 + (largura - 32) / passos + 1, base,
                                  fill=cor, outline=cor)
        self.create_rectangle(16, topo, largura - 16, base, outline=CORES["azul_medio"])
        for valor, texto in self.MARCAS:
            x = self._posicao(largura, valor)
            self.create_line(x, base, x, base + 4, fill=CORES["borda"])
            self.create_text(x, base + 12, text=texto, font=self.fontes["pequena"],
                             fill=CORES["texto_suave"])
        self.create_text(16, topo - 9, text="devagar", anchor="w",
                         font=self.fontes["pequena"], fill=CORES["texto_suave"])
        self.create_text(largura - 16, topo - 9, text="muito rápido", anchor="e",
                         font=self.fontes["pequena"], fill=CORES["texto_suave"])
        if self._cps is None:
            return
        x = self._posicao(largura, self._cps)
        self.create_polygon(x, topo - 3, x - 6, topo - 11, x + 6, topo - 11,
                            fill=CORES["azul_escuro"], outline=CORES["azul_escuro"])
        self.create_rectangle(x - 2, topo, x + 2, base, fill=CORES["cartao"],
                              outline=CORES["azul_escuro"])
