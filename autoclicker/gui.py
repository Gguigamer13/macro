"""Interface do Auto Clicker: abas, tema branco gelo + azul bebê."""

from __future__ import annotations

import queue
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from . import config, engine, tema, winapi
from .hotkeys import HotkeyListener
from .tema import CORES

BOTOES = [("Esquerdo", "left"), ("Direito", "right"), ("Meio", "middle")]
TECLAS = list(winapi.VK_CODES.keys())

# título, descrição e ícone de cada modo, na ordem em que aparecem na aba
MODOS = [
    (engine.MODE_CLICK, "Auto click",
     "Clica sem parar, no ritmo que você escolher na aba Tempos.", "repetir"),
    (engine.MODE_HOLD, "Segurar botão",
     "Aperta o botão e mantém pressionado até você mandar parar.", "mouse_cheio"),
    (engine.MODE_HOLD_CLICK, "Segurar + clique periódico",
     "Fica com o botão pressionado e, de tempos em tempos, solta e aperta de novo.",
     "relogio"),
]

DESTINOS = [
    (engine.TARGET_CURSOR, "Na posição atual do mouse",
     "O clique normal: acontece onde o cursor estiver naquele momento.", "cursor"),
    (engine.TARGET_WINDOW, "Em uma janela, em segundo plano",
     "O clique vai direto para a janela escolhida e o seu mouse continua livre.",
     "janela"),
]


class AutoClickerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.cfg = config.carregar()
        self.fila: "queue.Queue[tuple]" = queue.Queue()
        self.motor = engine.ClickEngine(on_count=self._contagem_da_thread,
                                        on_finish=self._fim_da_thread)
        self.atalhos = HotkeyListener(on_error=self._erro_de_atalho)
        self.janelas: list[dict] = []
        self.hwnd_alvo: int = 0
        self.titulo_alvo: str = ""
        self._linhas_modo: list[dict] = []
        self._linhas_destino: list[dict] = []

        root.title("Auto Clicker")
        root.configure(bg=CORES["gelo"])
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self._fechar)
        self.fontes = tema.aplicar_estilos(root)

        self._criar_variaveis()
        self._montar_interface()
        self._aplicar_atalhos()
        self._atualizar_lista_janelas()
        self._realcar_escolhas()
        self._atualizar_habilitados()
        self._atualizar_mapa()
        self._atualizar_cps()
        self.diagrama.mostrar(self.var_alvo.get())
        self._agendamento = self.root.after(40, self._processar_fila)

    # ------------------------------------------------------------------
    # Variáveis
    # ------------------------------------------------------------------

    def _criar_variaveis(self) -> None:
        c = self.cfg
        self.var_modo = tk.StringVar(value=c["mode"])
        self.var_botao = tk.StringVar(value=c["button"])
        self.var_alvo = tk.StringVar(value=c["target"])
        self.var_intervalo = tk.StringVar(value=str(c["interval_ms"]))
        self.var_variacao = tk.StringVar(value=str(c["jitter_pct"]))
        self.var_periodico = tk.StringVar(value=str(c["hold_click_every_ms"]))
        self.var_duracao = tk.StringVar(value=str(c["click_len_ms"]))
        self.var_limite = tk.StringVar(value=str(c["limit"]))
        self.var_x = tk.StringVar(value=str(c["x"]))
        self.var_y = tk.StringVar(value=str(c["y"]))
        self.var_janela = tk.StringVar()
        self.var_tecla_iniciar = tk.StringVar(value=c["hotkey_start"])
        self.var_tecla_capturar = tk.StringVar(value=c["hotkey_pick"])
        self.var_topmost = tk.BooleanVar(value=bool(c["sempre_visivel"]))
        self.var_status = tk.StringVar(value="Parado")
        self.var_cps = tk.StringVar(value="")
        self.var_contador = tk.StringVar(value="Cliques: 0")
        self.var_detalhe_alvo = tk.StringVar(value="Nenhuma janela selecionada.")

        self.var_intervalo.trace_add("write", lambda *_: self._atualizar_cps())
        self.var_modo.trace_add("write", lambda *_: self._modo_mudou())
        self.var_alvo.trace_add("write", lambda *_: self._modo_mudou())
        self.var_x.trace_add("write", lambda *_: self._atualizar_mapa())
        self.var_y.trace_add("write", lambda *_: self._atualizar_mapa())
        self.var_topmost.trace_add("write", lambda *_: self._aplicar_topmost())
        self._aplicar_topmost()
        self._atualizar_cps()

    # ------------------------------------------------------------------
    # Montagem da tela
    # ------------------------------------------------------------------

    def _montar_interface(self) -> None:
        self.cabecalho = tema.Cabecalho(self.root, self.fontes)
        self.cabecalho.pack(fill="x")

        self.abas = ttk.Notebook(self.root, style="Gelo.TNotebook")
        self.abas.pack(fill="both", expand=True, padx=14, pady=(10, 0))
        self.abas.add(self._aba_modo(), text="  Modo  ")
        self.abas.add(self._aba_tempos(), text="  Tempos  ")
        self.abas.add(self._aba_destino(), text="  Destino  ")
        self.abas.add(self._aba_janela(), text="  Janela  ")
        self.abas.add(self._aba_atalhos(), text="  Atalhos  ")

        self._rodape().pack(fill="x", padx=14, pady=(10, 0))
        tema.MarcaDagua(self.root, self.fontes).pack(fill="x", side="bottom")

    def _nova_aba(self) -> tk.Frame:
        quadro = tk.Frame(self.abas, bg=CORES["cartao"], width=628, height=436)
        quadro.pack_propagate(False)
        return quadro

    # -- aba 1: modo -----------------------------------------------------

    def _aba_modo(self) -> tk.Frame:
        aba = self._nova_aba()
        cartao = tema.Cartao(aba, self.fontes, "O que o macro faz", "repetir")
        cartao.pack(fill="x", padx=14, pady=(14, 10))
        for valor, titulo, descricao, icone in MODOS:
            self._linhas_modo.append(
                self._linha_escolha(cartao.corpo, self.var_modo, valor, titulo,
                                    descricao, icone))

        tema.Dica(aba, self.fontes,
                  "O modo \u201csegurar + clique periódico\u201d é o mesmo que ficar com o "
                  "botão apertado e dar um clique de vez em quando, sem largar.",
                  "repetir").pack(fill="x", side="bottom", padx=14, pady=14)

        cartao2 = tema.Cartao(aba, self.fontes, "Botão e parada", "mouse")
        cartao2.pack(fill="x", padx=14)
        linha = tk.Frame(cartao2.corpo, bg=CORES["cartao"])
        linha.pack(fill="x", pady=3)
        tema.rotulo(linha, "Botão do mouse", self.fontes, width=20,
                    anchor="w").pack(side="left")
        self.combo_botao = ttk.Combobox(linha, state="readonly", width=12,
                                        style="Gelo.TCombobox",
                                        values=[nome for nome, _ in BOTOES])
        self.combo_botao.set(next((nome for nome, valor in BOTOES
                                   if valor == self.var_botao.get()), BOTOES[0][0]))
        self.combo_botao.bind("<<ComboboxSelected>>", self._escolher_botao)
        self.combo_botao.pack(side="left")
        tema.rotulo(linha, "vale para os três modos", self.fontes,
                    "suave").pack(side="left", padx=(10, 0))
        self.ent_limite = self._campo(
            cartao2.corpo, "Parar depois de", self.var_limite, "cliques",
            "0 = sem limite")
        return aba

    # -- aba 2: tempos ---------------------------------------------------

    def _aba_tempos(self) -> tk.Frame:
        aba = self._nova_aba()
        cartao = tema.Cartao(aba, self.fontes, "Ritmo dos cliques", "relogio")
        cartao.pack(fill="x", padx=14, pady=(14, 10))
        self.ent_intervalo = self._campo(
            cartao.corpo, "Intervalo entre cliques", self.var_intervalo, "ms",
            "de um clique para o outro")
        tk.Label(cartao.corpo, textvariable=self.var_cps, font=self.fontes["forte"],
                 bg=CORES["cartao"], fg=CORES["azul_escuro"]).pack(anchor="w", pady=(2, 0))
        self.velocimetro = tema.Velocimetro(cartao.corpo, self.fontes)
        self.velocimetro.pack(fill="x", pady=(0, 6))
        self.ent_variacao = self._campo(
            cartao.corpo, "Variação aleatória", self.var_variacao, "%",
            "0 = sempre no mesmo ritmo")

        tema.Dica(aba, self.fontes,
                  "100 ms dá 10 cliques por segundo. Abaixo de 20 ms muitos programas "
                  "começam a perder cliques, então nem sempre vale a pena acelerar mais.",
                  "relogio").pack(fill="x", side="bottom", padx=14, pady=14)

        cartao2 = tema.Cartao(aba, self.fontes, "Ajustes finos", "repetir")
        cartao2.pack(fill="x", padx=14)
        self.ent_periodico = self._campo(
            cartao2.corpo, "Clicar a cada", self.var_periodico, "ms",
            "só no modo segurar + periódico")
        self.ent_duracao = self._campo(
            cartao2.corpo, "Duração de cada clique", self.var_duracao, "ms",
            "aumente se os cliques forem ignorados")
        return aba

    def _campo(self, pai: tk.Misc, titulo: str, variavel: tk.StringVar, unidade: str,
               dica: str) -> tk.Entry:
        linha = tk.Frame(pai, bg=CORES["cartao"])
        linha.pack(fill="x", pady=3)
        tema.rotulo(linha, titulo, self.fontes, width=20, anchor="w").pack(side="left")
        campo = tema.entrada(linha, variavel, self.fontes)
        campo.pack(side="left")
        tema.rotulo(linha, unidade, self.fontes, "suave").pack(side="left", padx=(6, 10))
        tema.rotulo(linha, dica, self.fontes, "suave").pack(side="left")
        return campo

    # -- aba 3: destino --------------------------------------------------

    def _aba_destino(self) -> tk.Frame:
        aba = self._nova_aba()
        cartao = tema.Cartao(aba, self.fontes, "Para onde vão os cliques", "alvo")
        cartao.pack(fill="x", padx=14, pady=(14, 0))
        for valor, titulo, descricao, icone in DESTINOS:
            self._linhas_destino.append(
                self._linha_escolha(cartao.corpo, self.var_alvo, valor, titulo,
                                    descricao, icone))
        self.diagrama = tema.Diagrama(cartao.corpo, self.fontes)
        self.diagrama.pack(fill="x", pady=(10, 0))

        tema.Dica(aba, self.fontes,
                  "No modo em segundo plano escolha a janela e o ponto do clique na aba "
                  "Janela, ao lado.", "janela").pack(fill="x", side="bottom",
                                                     padx=14, pady=14)
        return aba

    # -- aba 4: janela alvo ----------------------------------------------

    def _aba_janela(self) -> tk.Frame:
        aba = self._nova_aba()
        cartao = tema.Cartao(aba, self.fontes, "Janela e ponto do clique", "janela")
        cartao.pack(fill="x", padx=14, pady=(14, 0))
        corpo = cartao.corpo

        linha1 = tk.Frame(corpo, bg=CORES["cartao"])
        linha1.pack(fill="x")
        self.combo_janelas = ttk.Combobox(linha1, textvariable=self.var_janela,
                                          state="readonly", width=46,
                                          style="Gelo.TCombobox")
        self.combo_janelas.pack(side="left")
        self.combo_janelas.bind("<<ComboboxSelected>>", self._selecionar_janela_da_lista)
        self.btn_atualizar = tema.Botao(linha1, self.fontes, "Atualizar",
                                        self._atualizar_lista_janelas, padx=10)
        self.btn_atualizar.pack(side="left", padx=(8, 0))

        linha2 = tk.Frame(corpo, bg=CORES["cartao"])
        linha2.pack(fill="x", pady=(8, 0))
        self.btn_capturar = tema.Botao(linha2, self.fontes, "Capturar janela e ponto",
                                       self._capturar_ponto, principal=True,
                                       padx=10, pady=3)
        self.btn_capturar.pack(side="left")
        tema.rotulo(linha2, "X", self.fontes, "suave").pack(side="left", padx=(12, 3))
        self.ent_x = tema.entrada(linha2, self.var_x, self.fontes, largura=7)
        self.ent_x.pack(side="left")
        tema.rotulo(linha2, "Y", self.fontes, "suave").pack(side="left", padx=(8, 3))
        self.ent_y = tema.entrada(linha2, self.var_y, self.fontes, largura=7)
        self.ent_y.pack(side="left")

        linha3 = tk.Frame(corpo, bg=CORES["cartao"])
        linha3.pack(fill="x", pady=(8, 0))
        self.btn_centro = tema.Botao(linha3, self.fontes, "Usar o centro da janela",
                                     self._usar_centro, padx=8)
        self.btn_centro.pack(side="left")
        self.btn_testar = tema.Botao(linha3, self.fontes, "Testar 1 clique",
                                     self._testar_clique, padx=8)
        self.btn_testar.pack(side="left", padx=(8, 0))
        tk.Label(linha3, textvariable=self.var_detalhe_alvo, font=self.fontes["pequena"],
                 bg=CORES["cartao"], fg=CORES["texto_suave"], anchor="w",
                 justify="left").pack(side="left", padx=(12, 0))

        self.mapa = tema.MapaAlvo(corpo, self.fontes)
        self.mapa.pack(fill="x", pady=(10, 0))

        tema.Dica(aba, self.fontes,
                  "Use “Testar 1 clique” antes de soltar o macro: dá para ver na hora se "
                  "a janela aceita clique em segundo plano.",
                  "alvo").pack(fill="x", side="bottom", padx=14, pady=14)
        return aba

    # -- aba 5: atalhos --------------------------------------------------

    def _aba_atalhos(self) -> tk.Frame:
        aba = self._nova_aba()
        cartao = tema.Cartao(aba, self.fontes, "Teclas de atalho", "teclado")
        cartao.pack(fill="x", padx=14, pady=(14, 10))

        linha1 = tk.Frame(cartao.corpo, bg=CORES["cartao"])
        linha1.pack(fill="x", pady=3)
        tema.rotulo(linha1, "Iniciar / parar", self.fontes, width=20,
                    anchor="w").pack(side="left")
        combo1 = ttk.Combobox(linha1, textvariable=self.var_tecla_iniciar, values=TECLAS,
                              state="readonly", width=12, style="Gelo.TCombobox")
        combo1.pack(side="left")
        combo1.bind("<<ComboboxSelected>>", lambda _e: self._aplicar_atalhos())
        tema.rotulo(linha1, "mesmo com outro programa na frente",
                    self.fontes, "suave").pack(side="left", padx=(10, 0))

        linha2 = tk.Frame(cartao.corpo, bg=CORES["cartao"])
        linha2.pack(fill="x", pady=3)
        tema.rotulo(linha2, "Capturar janela e ponto", self.fontes, width=20,
                    anchor="w").pack(side="left")
        combo2 = ttk.Combobox(linha2, textvariable=self.var_tecla_capturar, values=TECLAS,
                              state="readonly", width=12, style="Gelo.TCombobox")
        combo2.pack(side="left")
        combo2.bind("<<ComboboxSelected>>", lambda _e: self._aplicar_atalhos())
        tema.rotulo(linha2, "passe o mouse no ponto e aperte a tecla",
                    self.fontes, "suave").pack(side="left", padx=(10, 0))

        tema.Dica(aba, self.fontes,
                  "O atalho de iniciar/parar funciona mesmo com outro programa na frente — "
                  "é assim que você sai do modo \u201csegurar\u201d sem ficar com o botão preso.",
                  "teclado").pack(fill="x", side="bottom", padx=14, pady=14)

        cartao2 = tema.Cartao(aba, self.fontes, "Preferências", "janela")
        cartao2.pack(fill="x", padx=14)
        tk.Checkbutton(cartao2.corpo, text="Manter esta janela sempre visível",
                       variable=self.var_topmost, font=self.fontes["normal"],
                       bg=CORES["cartao"], fg=CORES["texto"], selectcolor=CORES["cartao"],
                       activebackground=CORES["cartao"], activeforeground=CORES["azul_escuro"],
                       relief="flat", bd=0, highlightthickness=0, anchor="w",
                       cursor="hand2").pack(fill="x")
        tema.rotulo(cartao2.corpo,
                    "As suas escolhas são salvas sozinhas ao fechar o programa, em\n"
                    f"{config.caminho()}",
                    self.fontes, "suave", justify="left").pack(anchor="w", pady=(8, 0))
        return aba

    # -- linhas de escolha (modo / destino) ------------------------------

    def _linha_escolha(self, pai: tk.Misc, variavel: tk.StringVar, valor: str,
                       titulo: str, descricao: str, icone: str) -> dict:
        linha = tk.Frame(pai, bg=CORES["cartao"], highlightthickness=1,
                         highlightbackground=CORES["cartao"], cursor="hand2")
        linha.pack(fill="x", pady=2)

        desenho = tk.Canvas(linha, width=30, height=34, bg=CORES["cartao"],
                            highlightthickness=0)
        if icone == "mouse_cheio":
            tema.icone_mouse(desenho, 15, 17, CORES["azul_escuro"], cheio=True)
        else:
            tema.ICONES[icone](desenho, 15, 17, CORES["azul_escuro"])
        desenho.pack(side="left", padx=(6, 4), pady=4)

        textos = tk.Frame(linha, bg=CORES["cartao"])
        textos.pack(side="left", fill="x", expand=True, pady=4)
        botao = tema.radio(textos, titulo, variavel, valor, self.fontes)
        botao.pack(fill="x")
        legenda = tema.rotulo(textos, descricao, self.fontes, "suave",
                              anchor="w", justify="left")
        legenda.pack(fill="x", padx=(22, 0))

        for widget in (linha, desenho, textos, legenda):
            widget.bind("<Button-1>", lambda _e, v=valor: variavel.set(v))
        return {"quadro": linha, "valor": valor, "variavel": variavel,
                "pintar": [linha, desenho, textos, botao, legenda]}

    def _realcar_escolhas(self) -> None:
        """Pinta de azul bebê a opção selecionada em cada lista."""
        for linha in self._linhas_modo + self._linhas_destino:
            escolhida = linha["variavel"].get() == linha["valor"]
            fundo = CORES["azul_claro"] if escolhida else CORES["cartao"]
            borda = CORES["azul_medio"] if escolhida else CORES["cartao"]
            linha["quadro"].configure(highlightbackground=borda)
            for widget in linha["pintar"]:
                widget.configure(bg=fundo)
                if isinstance(widget, tk.Radiobutton):
                    widget.configure(activebackground=fundo, selectcolor=fundo)

    def _modo_mudou(self) -> None:
        self._realcar_escolhas()
        self._atualizar_habilitados()
        if hasattr(self, "diagrama"):
            self.diagrama.mostrar(self.var_alvo.get())

    def _escolher_botao(self, _evento=None) -> None:
        self.var_botao.set(dict(BOTOES)[self.combo_botao.get()])

    # -- rodapé ----------------------------------------------------------

    def _rodape(self) -> tk.Frame:
        rodape = tk.Frame(self.root, bg=CORES["gelo"])

        esquerda = tk.Frame(rodape, bg=CORES["gelo"])
        esquerda.pack(side="left")
        self.luz = tema.Indicador(esquerda, CORES["gelo"])
        self.luz.pack(side="left", padx=(0, 6))
        self.lbl_status = tk.Label(esquerda, textvariable=self.var_status,
                                   font=self.fontes["botao"], bg=CORES["gelo"],
                                   fg=CORES["texto"])
        self.lbl_status.pack(side="left")
        tk.Label(esquerda, textvariable=self.var_contador, font=self.fontes["normal"],
                 bg=CORES["gelo"], fg=CORES["texto_suave"]).pack(side="left", padx=(12, 0))

        self.btn_parar = tema.Botao(rodape, self.fontes, "PARAR", self.parar,
                                    padx=18, pady=6, state="disabled")
        self.btn_parar.pack(side="right")
        self.btn_iniciar = tema.Botao(rodape, self.fontes, "INICIAR", self.iniciar,
                                      principal=True, padx=22, pady=6)
        self.btn_iniciar.pack(side="right", padx=(0, 8))
        return rodape

    # ------------------------------------------------------------------
    # Estado da interface
    # ------------------------------------------------------------------

    def _aplicar_topmost(self) -> None:
        try:
            self.root.attributes("-topmost", bool(self.var_topmost.get()))
        except tk.TclError:
            pass

    def _atualizar_cps(self) -> None:
        cps = None
        try:
            ms = int(self.var_intervalo.get())
            if ms > 0:
                cps = 1000 / ms
        except (ValueError, ZeroDivisionError):
            cps = None
        self.var_cps.set(f"≈ {cps:.1f} cliques por segundo" if cps else "")
        if hasattr(self, "velocimetro"):
            self.velocimetro.definir(cps)

    def _atualizar_habilitados(self) -> None:
        rodando = self.motor.running
        modo = self.var_modo.get()
        janela = self.var_alvo.get() == engine.TARGET_WINDOW

        def estado(ativo: bool) -> str:
            return "normal" if ativo and not rodando else "disabled"

        self.ent_intervalo.configure(state=estado(modo == engine.MODE_CLICK))
        self.ent_variacao.configure(state=estado(modo == engine.MODE_CLICK))
        self.ent_periodico.configure(state=estado(modo == engine.MODE_HOLD_CLICK))
        self.ent_duracao.configure(state=estado(True))
        self.ent_limite.configure(state=estado(True))
        self.combo_botao.configure(state="readonly" if not rodando else "disabled")
        self.combo_janelas.configure(
            state="readonly" if janela and not rodando else "disabled")
        for widget in (self.btn_atualizar, self.btn_centro, self.ent_x, self.ent_y,
                       self.btn_capturar, self.btn_testar):
            widget.configure(state=estado(janela))
        self.btn_iniciar.configure(state="disabled" if rodando else "normal")
        self.btn_parar.configure(state="normal" if rodando else "disabled")

    def _definir_status(self, texto: str, cor: str = CORES["texto"]) -> None:
        self.var_status.set(texto)
        self.lbl_status.configure(foreground=cor)
        self.luz.definir(cor if cor != CORES["texto"] else CORES["texto_suave"])

    # ------------------------------------------------------------------
    # Janela alvo
    # ------------------------------------------------------------------

    def _atualizar_lista_janelas(self) -> None:
        if not winapi.IS_WINDOWS:
            return
        self.janelas = winapi.list_windows()
        self.combo_janelas.configure(values=[self._rotulo(j) for j in self.janelas])
        for indice, janela in enumerate(self.janelas):
            if janela["hwnd"] == self.hwnd_alvo:
                self.combo_janelas.current(indice)
                return
        if self.hwnd_alvo and not winapi.is_window(self.hwnd_alvo):
            self.hwnd_alvo = 0
            self.var_janela.set("")
            self.var_detalhe_alvo.set("A janela escolhida foi fechada.")
            self._atualizar_mapa()

    @staticmethod
    def _rotulo(janela: dict) -> str:
        titulo = janela["title"]
        if len(titulo) > 52:
            titulo = titulo[:49] + "..."
        return f"{janela['process'] or '?'} — {titulo}"

    def _selecionar_janela_da_lista(self, _evento=None) -> None:
        indice = self.combo_janelas.current()
        if 0 <= indice < len(self.janelas):
            janela = self.janelas[indice]
            self.hwnd_alvo = janela["hwnd"]
            self.titulo_alvo = janela["title"]
            if not self.var_x.get().strip() or (self.var_x.get() == "0"
                                                and self.var_y.get() == "0"):
                self._usar_centro()
            self._descrever_alvo()

    def _usar_centro(self) -> None:
        if not self._exigir_janela():
            return
        largura, altura = winapi.get_client_size(self.hwnd_alvo)
        self.var_x.set(str(largura // 2))
        self.var_y.set(str(altura // 2))
        self._descrever_alvo()

    def _capturar_ponto(self) -> None:
        if not winapi.IS_WINDOWS:
            return
        try:
            hwnd, x, y = winapi.window_at_cursor()
        except winapi.WinApiError as erro:
            messagebox.showerror("Auto Clicker", str(erro), parent=self.root)
            return
        if hwnd == self._proprio_hwnd():
            self._definir_status("Isso é a janela do próprio Auto Clicker",
                                 CORES["ambar"])
            return
        self.hwnd_alvo = hwnd
        self.titulo_alvo = winapi.get_window_title(hwnd)
        self.var_x.set(str(x))
        self.var_y.set(str(y))
        self.var_alvo.set(engine.TARGET_WINDOW)
        self._atualizar_lista_janelas()
        self._descrever_alvo()
        self._definir_status("Ponto capturado", CORES["verde"])

    def _proprio_hwnd(self) -> int:
        try:
            return int(winapi.user32.GetAncestor(self.root.winfo_id(), winapi.GA_ROOT))
        except Exception:
            return 0

    def _descrever_alvo(self) -> None:
        if not self.hwnd_alvo:
            self.var_detalhe_alvo.set("Nenhuma janela selecionada.")
        else:
            try:
                alvo, _tx, _ty = winapi.resolve_click_target(
                    self.hwnd_alvo, self._inteiro(self.var_x, "X"),
                    self._inteiro(self.var_y, "Y"))
                aviso = "\n⚠ a janela está minimizada" if winapi.is_minimized(
                    self.hwnd_alvo) else ""
                self.var_detalhe_alvo.set(
                    f"recebe o clique:\n{winapi.get_class_name(alvo)}{aviso}")
            except (ValueError, winapi.WinApiError) as erro:
                self.var_detalhe_alvo.set(str(erro))
        self._atualizar_mapa()

    def _atualizar_mapa(self) -> None:
        mapa = getattr(self, "mapa", None)
        if mapa is None:
            return
        if not self.hwnd_alvo or not winapi.is_window(self.hwnd_alvo):
            mapa.limpar("Escolha uma janela para ver onde o clique vai cair.")
            return
        try:
            largura, altura = winapi.get_client_size(self.hwnd_alvo)
            mapa.mostrar(largura, altura, self._inteiro(self.var_x, "X"),
                         self._inteiro(self.var_y, "Y"), self.titulo_alvo)
        except (ValueError, winapi.WinApiError):
            mapa.limpar("Confira os valores de X e Y.")

    def _exigir_janela(self) -> bool:
        if not self.hwnd_alvo or not winapi.is_window(self.hwnd_alvo):
            messagebox.showwarning(
                "Auto Clicker",
                "Escolha uma janela na lista ou use o botão de capturar.",
                parent=self.root)
            return False
        return True

    # ------------------------------------------------------------------
    # Início / parada
    # ------------------------------------------------------------------

    def _inteiro(self, variavel: tk.StringVar, nome: str) -> int:
        texto = variavel.get().strip().replace(",", ".")
        try:
            return int(float(texto))
        except ValueError:
            raise ValueError(f"O campo '{nome}' precisa ser um número.") from None

    def _coletar_configuracao(self) -> engine.ClickSettings:
        ajustes = engine.ClickSettings(
            mode=self.var_modo.get(),
            button=self.var_botao.get(),
            target=self.var_alvo.get(),
            interval_ms=self._inteiro(self.var_intervalo, "Intervalo entre cliques"),
            jitter_pct=self._inteiro(self.var_variacao, "Variação aleatória"),
            hold_click_every_ms=self._inteiro(self.var_periodico, "Clicar a cada"),
            click_len_ms=self._inteiro(self.var_duracao, "Duração de cada clique"),
            limit=self._inteiro(self.var_limite, "Parar depois de"),
            hwnd=self.hwnd_alvo,
            x=self._inteiro(self.var_x, "ponto X"),
            y=self._inteiro(self.var_y, "ponto Y"),
            window_title=self.titulo_alvo,
        )
        ajustes.validate()
        return ajustes

    def iniciar(self) -> None:
        if self.motor.running:
            return
        try:
            ajustes = self._coletar_configuracao()
        except ValueError as erro:
            messagebox.showerror("Auto Clicker", str(erro), parent=self.root)
            return
        if ajustes.target == engine.TARGET_WINDOW and winapi.is_minimized(ajustes.hwnd):
            if not messagebox.askyesno(
                    "Auto Clicker",
                    "A janela escolhida está minimizada e talvez ignore os cliques.\n"
                    "Quer tentar mesmo assim?", parent=self.root):
                return
        self.motor.start(ajustes)
        self.var_contador.set("Cliques: 0")
        self._definir_status(engine.MODE_LABELS[ajustes.mode] + " rodando", CORES["verde"])
        self.cabecalho.animar(True)
        self._atualizar_habilitados()

    def parar(self) -> None:
        if self.motor.running:
            self.motor.stop(wait=False)

    def alternar(self) -> None:
        self.parar() if self.motor.running else self.iniciar()

    def _testar_clique(self) -> None:
        try:
            engine.single_click(self._coletar_configuracao())
            self._definir_status("Clique de teste enviado", CORES["verde"])
        except (ValueError, winapi.WinApiError) as erro:
            messagebox.showerror("Auto Clicker", str(erro), parent=self.root)

    # ------------------------------------------------------------------
    # Conversa com as outras threads
    # ------------------------------------------------------------------

    def _contagem_da_thread(self, total: int) -> None:
        self.fila.put(("contagem", total))

    def _fim_da_thread(self, motivo: str, erro: Optional[str]) -> None:
        self.fila.put(("fim", motivo, erro))

    def _erro_de_atalho(self, mensagem: str) -> None:
        self.fila.put(("aviso", mensagem))

    def _processar_fila(self) -> None:
        try:
            while True:
                evento = self.fila.get_nowait()
                if evento[0] == "contagem":
                    self.var_contador.set(f"Cliques: {evento[1]}")
                elif evento[0] == "fim":
                    _, motivo, erro = evento
                    self.cabecalho.animar(False)
                    if erro:
                        self._definir_status("Erro", CORES["vermelho"])
                        messagebox.showerror("Auto Clicker", erro, parent=self.root)
                    elif motivo == "limite":
                        self._definir_status("Terminou (limite de cliques)")
                    else:
                        self._definir_status("Parado")
                    self._atualizar_habilitados()
                elif evento[0] == "aviso":
                    self._definir_status(evento[1], CORES["ambar"])
                elif evento[0] == "alternar":
                    self.alternar()
                elif evento[0] == "capturar":
                    self._capturar_ponto()
        except queue.Empty:
            pass
        self._agendamento = self.root.after(40, self._processar_fila)

    # ------------------------------------------------------------------
    # Atalhos globais
    # ------------------------------------------------------------------

    def _aplicar_atalhos(self) -> None:
        iniciar = self.var_tecla_iniciar.get()
        capturar = self.var_tecla_capturar.get()
        if iniciar == capturar:
            self._definir_status("Os dois atalhos não podem usar a mesma tecla",
                                 CORES["ambar"])
            return
        self.atalhos.set_hotkeys({
            iniciar: lambda: self.fila.put(("alternar",)),
            capturar: lambda: self.fila.put(("capturar",)),
        })
        self.btn_iniciar.configure(text=f"INICIAR  ({iniciar})")
        self.btn_parar.configure(text=f"PARAR  ({iniciar})")
        self.btn_capturar.configure(text=f"Capturar janela e ponto  ({capturar})")

    # ------------------------------------------------------------------

    def _salvar_configuracao(self) -> None:
        def numero(variavel: tk.StringVar, padrao: int) -> int:
            try:
                return int(float(variavel.get().strip().replace(",", ".")))
            except ValueError:
                return padrao

        config.salvar({
            "mode": self.var_modo.get(),
            "button": self.var_botao.get(),
            "target": self.var_alvo.get(),
            "interval_ms": numero(self.var_intervalo, 100),
            "jitter_pct": numero(self.var_variacao, 0),
            "hold_click_every_ms": numero(self.var_periodico, 2000),
            "click_len_ms": numero(self.var_duracao, 30),
            "limit": numero(self.var_limite, 0),
            "x": numero(self.var_x, 0),
            "y": numero(self.var_y, 0),
            "hotkey_start": self.var_tecla_iniciar.get(),
            "hotkey_pick": self.var_tecla_capturar.get(),
            "sempre_visivel": bool(self.var_topmost.get()),
        })

    def encerrar(self) -> None:
        """Para tudo que roda fora da interface (threads, animação, agendamentos)."""
        self.motor.stop()
        self.atalhos.stop()
        self.cabecalho.parar_animacao()
        try:
            self.root.after_cancel(self._agendamento)
        except (tk.TclError, AttributeError):
            pass

    def _fechar(self) -> None:
        self.encerrar()
        self._salvar_configuracao()
        self.root.destroy()


def main() -> int:
    if not winapi.IS_WINDOWS:
        print("O Auto Clicker usa a API do Windows e só roda no Windows.")
        return 1
    try:  # deixa a janela nítida em telas com escala (125%, 150%...)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    AutoClickerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
