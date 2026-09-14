"""Interface do Auto Clicker (tkinter)."""

from __future__ import annotations

import queue
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from . import config, engine, winapi
from .hotkeys import HotkeyListener

BOTOES = [("Esquerdo", "left"), ("Direito", "right"), ("Meio", "middle")]
TECLAS = list(winapi.VK_CODES.keys())


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

        root.title("Auto Clicker")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self._fechar)

        self._criar_variaveis()
        self._montar_interface()
        self._aplicar_atalhos()
        self._atualizar_lista_janelas()
        self._atualizar_habilitados()
        self._agendamento = self.root.after(40, self._processar_fila)

    # ------------------------------------------------------------------
    # Construção da tela
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
        self.var_modo.trace_add("write", lambda *_: self._atualizar_habilitados())
        self.var_alvo.trace_add("write", lambda *_: self._atualizar_habilitados())
        self.var_topmost.trace_add("write", lambda *_: self._aplicar_topmost())
        self._aplicar_topmost()
        self._atualizar_cps()

    def _montar_interface(self) -> None:
        principal = ttk.Frame(self.root, padding=10)
        principal.grid(row=0, column=0, sticky="nsew")

        self._secao_modo(principal).grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._secao_destino(principal).grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self._secao_atalhos(principal).grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self._secao_controles(principal).grid(row=3, column=0, sticky="ew")

    def _secao_modo(self, pai: ttk.Frame) -> ttk.Widget:
        caixa = ttk.LabelFrame(pai, text=" 1. O que o macro faz ", padding=10)

        ttk.Radiobutton(caixa, text="Auto click — clica sem parar",
                        variable=self.var_modo, value=engine.MODE_CLICK
                        ).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Radiobutton(caixa, text="Segurar botão — mantém o botão pressionado",
                        variable=self.var_modo, value=engine.MODE_HOLD
                        ).grid(row=1, column=0, columnspan=4, sticky="w")
        ttk.Radiobutton(caixa, text="Segurar + clique periódico — segura e clica de tempos em tempos",
                        variable=self.var_modo, value=engine.MODE_HOLD_CLICK
                        ).grid(row=2, column=0, columnspan=4, sticky="w")

        ttk.Separator(caixa, orient="horizontal").grid(
            row=3, column=0, columnspan=4, sticky="ew", pady=8)

        ttk.Label(caixa, text="Botão do mouse:").grid(row=4, column=0, sticky="w")
        combo = ttk.Combobox(caixa, state="readonly", width=12,
                             values=[nome for nome, _ in BOTOES])
        combo.set(next((nome for nome, valor in BOTOES if valor == self.var_botao.get()),
                       BOTOES[0][0]))
        combo.bind("<<ComboboxSelected>>",
                   lambda _e: self.var_botao.set(dict((n, v) for n, v in BOTOES)[combo.get()]))
        combo.grid(row=4, column=1, sticky="w", padx=(6, 0))

        ttk.Label(caixa, text="Intervalo entre cliques:").grid(row=5, column=0, sticky="w", pady=(6, 0))
        self.ent_intervalo = ttk.Entry(caixa, textvariable=self.var_intervalo, width=8)
        self.ent_intervalo.grid(row=5, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        ttk.Label(caixa, text="ms").grid(row=5, column=2, sticky="w")
        ttk.Label(caixa, textvariable=self.var_cps, foreground="#555").grid(
            row=5, column=3, sticky="w", padx=(6, 0))

        ttk.Label(caixa, text="Variação aleatória:").grid(row=6, column=0, sticky="w", pady=(6, 0))
        self.ent_variacao = ttk.Entry(caixa, textvariable=self.var_variacao, width=8)
        self.ent_variacao.grid(row=6, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        ttk.Label(caixa, text="%  (deixa o ritmo menos robótico)").grid(
            row=6, column=2, columnspan=2, sticky="w")

        ttk.Label(caixa, text="Clicar a cada:").grid(row=7, column=0, sticky="w", pady=(6, 0))
        self.ent_periodico = ttk.Entry(caixa, textvariable=self.var_periodico, width=8)
        self.ent_periodico.grid(row=7, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        ttk.Label(caixa, text="ms  (enquanto segura o botão)").grid(
            row=7, column=2, columnspan=2, sticky="w")

        ttk.Label(caixa, text="Duração de cada clique:").grid(row=8, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(caixa, textvariable=self.var_duracao, width=8).grid(
            row=8, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        ttk.Label(caixa, text="ms").grid(row=8, column=2, sticky="w")

        ttk.Label(caixa, text="Parar depois de:").grid(row=9, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(caixa, textvariable=self.var_limite, width=8).grid(
            row=9, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        ttk.Label(caixa, text="cliques  (0 = sem limite)").grid(
            row=9, column=2, columnspan=2, sticky="w")
        return caixa

    def _secao_destino(self, pai: ttk.Frame) -> ttk.Widget:
        caixa = ttk.LabelFrame(pai, text=" 2. Onde os cliques vão cair ", padding=10)

        ttk.Radiobutton(caixa, text="Na posição atual do mouse (clique normal)",
                        variable=self.var_alvo, value=engine.TARGET_CURSOR
                        ).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Radiobutton(caixa, text="Em uma janela escolhida, em segundo plano (mouse continua livre)",
                        variable=self.var_alvo, value=engine.TARGET_WINDOW
                        ).grid(row=1, column=0, columnspan=3, sticky="w")

        self.combo_janelas = ttk.Combobox(caixa, textvariable=self.var_janela,
                                          state="readonly", width=52)
        self.combo_janelas.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.combo_janelas.bind("<<ComboboxSelected>>", self._selecionar_janela_da_lista)
        self.btn_atualizar = ttk.Button(caixa, text="Atualizar",
                                        command=self._atualizar_lista_janelas)
        self.btn_atualizar.grid(row=2, column=2, sticky="w", padx=(6, 0), pady=(8, 0))

        linha = ttk.Frame(caixa)
        linha.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.btn_capturar = ttk.Button(linha, text="Capturar janela e ponto",
                                       command=self._capturar_ponto)
        self.btn_capturar.pack(side="left")
        ttk.Label(linha, text="  ponto X:").pack(side="left")
        self.ent_x = ttk.Entry(linha, textvariable=self.var_x, width=7)
        self.ent_x.pack(side="left", padx=(4, 0))
        ttk.Label(linha, text=" Y:").pack(side="left")
        self.ent_y = ttk.Entry(linha, textvariable=self.var_y, width=7)
        self.ent_y.pack(side="left", padx=(4, 0))

        linha2 = ttk.Frame(caixa)
        linha2.grid(row=4, column=0, columnspan=3, sticky="w", pady=(6, 0))
        self.btn_centro = ttk.Button(linha2, text="Usar o centro da janela",
                                     command=self._usar_centro)
        self.btn_centro.pack(side="left")
        self.btn_testar = ttk.Button(linha2, text="Testar 1 clique",
                                     command=self._testar_clique)
        self.btn_testar.pack(side="left", padx=(6, 0))

        ttk.Label(caixa, textvariable=self.var_detalhe_alvo, foreground="#555",
                  wraplength=430, justify="left").grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))
        return caixa

    def _secao_atalhos(self, pai: ttk.Frame) -> ttk.Widget:
        caixa = ttk.LabelFrame(pai, text=" 3. Atalhos do teclado ", padding=10)

        ttk.Label(caixa, text="Iniciar / parar:").grid(row=0, column=0, sticky="w")
        combo1 = ttk.Combobox(caixa, textvariable=self.var_tecla_iniciar, values=TECLAS,
                              state="readonly", width=10)
        combo1.grid(row=0, column=1, sticky="w", padx=(6, 12))
        combo1.bind("<<ComboboxSelected>>", lambda _e: self._aplicar_atalhos())

        ttk.Label(caixa, text="Capturar janela e ponto:").grid(row=0, column=2, sticky="w")
        combo2 = ttk.Combobox(caixa, textvariable=self.var_tecla_capturar, values=TECLAS,
                              state="readonly", width=10)
        combo2.grid(row=0, column=3, sticky="w", padx=(6, 0))
        combo2.bind("<<ComboboxSelected>>", lambda _e: self._aplicar_atalhos())

        ttk.Checkbutton(caixa, text="Manter esta janela sempre visível",
                        variable=self.var_topmost).grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))
        return caixa

    def _secao_controles(self, pai: ttk.Frame) -> ttk.Widget:
        caixa = ttk.Frame(pai)
        self.btn_iniciar = ttk.Button(caixa, text="INICIAR", command=self.iniciar)
        self.btn_iniciar.grid(row=0, column=0, ipadx=18, ipady=4)
        self.btn_parar = ttk.Button(caixa, text="PARAR", command=self.parar, state="disabled")
        self.btn_parar.grid(row=0, column=1, ipadx=18, ipady=4, padx=(8, 0))

        self.lbl_status = ttk.Label(caixa, textvariable=self.var_status,
                                    font=("Segoe UI", 10, "bold"))
        self.lbl_status.grid(row=0, column=2, sticky="e", padx=(16, 0))
        ttk.Label(caixa, textvariable=self.var_contador, foreground="#555").grid(
            row=0, column=3, sticky="e", padx=(12, 0))
        return caixa

    # ------------------------------------------------------------------
    # Estado da interface
    # ------------------------------------------------------------------

    def _aplicar_topmost(self) -> None:
        try:
            self.root.attributes("-topmost", bool(self.var_topmost.get()))
        except tk.TclError:
            pass

    def _atualizar_cps(self) -> None:
        try:
            ms = int(self.var_intervalo.get())
            self.var_cps.set(f"≈ {1000 / ms:.1f} cliques por segundo" if ms > 0 else "")
        except (ValueError, ZeroDivisionError):
            self.var_cps.set("")

    def _atualizar_habilitados(self) -> None:
        rodando = self.motor.running
        modo = self.var_modo.get()
        janela = self.var_alvo.get() == engine.TARGET_WINDOW

        def estado(ativo: bool) -> str:
            return "normal" if ativo and not rodando else "disabled"

        self.ent_intervalo.configure(state=estado(modo == engine.MODE_CLICK))
        self.ent_variacao.configure(state=estado(modo == engine.MODE_CLICK))
        self.ent_periodico.configure(state=estado(modo == engine.MODE_HOLD_CLICK))
        self.combo_janelas.configure(
            state="readonly" if janela and not rodando else "disabled")
        for widget in (self.btn_atualizar, self.btn_centro, self.ent_x, self.ent_y,
                       self.btn_capturar, self.btn_testar):
            widget.configure(state=estado(janela))
        self.btn_iniciar.configure(state="disabled" if rodando else "normal")
        self.btn_parar.configure(state="normal" if rodando else "disabled")

    def _definir_status(self, texto: str, cor: str = "#333") -> None:
        self.var_status.set(texto)
        self.lbl_status.configure(foreground=cor)

    # ------------------------------------------------------------------
    # Janela alvo
    # ------------------------------------------------------------------

    def _atualizar_lista_janelas(self) -> None:
        if not winapi.IS_WINDOWS:
            return
        self.janelas = winapi.list_windows()
        rotulos = [self._rotulo(j) for j in self.janelas]
        self.combo_janelas.configure(values=rotulos)
        # mantém selecionada a janela que já estava escolhida, se ainda existir
        for indice, janela in enumerate(self.janelas):
            if janela["hwnd"] == self.hwnd_alvo:
                self.combo_janelas.current(indice)
                return
        if self.hwnd_alvo and not winapi.is_window(self.hwnd_alvo):
            self.hwnd_alvo = 0
            self.var_janela.set("")
            self.var_detalhe_alvo.set("A janela que estava escolhida foi fechada.")

    @staticmethod
    def _rotulo(janela: dict) -> str:
        titulo = janela["title"]
        if len(titulo) > 60:
            titulo = titulo[:57] + "..."
        processo = janela["process"] or "?"
        return f"{processo} — {titulo}"

    def _selecionar_janela_da_lista(self, _evento=None) -> None:
        indice = self.combo_janelas.current()
        if 0 <= indice < len(self.janelas):
            janela = self.janelas[indice]
            self.hwnd_alvo = janela["hwnd"]
            self.titulo_alvo = janela["title"]
            if not self.var_x.get().strip() or (self.var_x.get() == "0" and self.var_y.get() == "0"):
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
        """Pega a janela embaixo do cursor e o ponto exato dentro dela."""
        if not winapi.IS_WINDOWS:
            return
        try:
            hwnd, x, y = winapi.window_at_cursor()
        except winapi.WinApiError as erro:
            messagebox.showerror("Auto Clicker", str(erro), parent=self.root)
            return
        if hwnd == self._proprio_hwnd():
            self._definir_status("Isso é a janela do próprio Auto Clicker", "#b45309")
            return
        self.hwnd_alvo = hwnd
        self.titulo_alvo = winapi.get_window_title(hwnd)
        self.var_x.set(str(x))
        self.var_y.set(str(y))
        self.var_alvo.set(engine.TARGET_WINDOW)
        self._atualizar_lista_janelas()
        self._descrever_alvo()
        self._definir_status("Ponto capturado", "#15803d")

    def _proprio_hwnd(self) -> int:
        try:
            return int(winapi.user32.GetAncestor(self.root.winfo_id(), winapi.GA_ROOT))
        except Exception:
            return 0

    def _descrever_alvo(self) -> None:
        if not self.hwnd_alvo:
            self.var_detalhe_alvo.set("Nenhuma janela selecionada.")
            return
        try:
            x, y = self._inteiro(self.var_x, "X"), self._inteiro(self.var_y, "Y")
            alvo, _tx, _ty = winapi.resolve_click_target(self.hwnd_alvo, x, y)
            classe = winapi.get_class_name(alvo)
            aviso = "  ⚠ janela minimizada" if winapi.is_minimized(self.hwnd_alvo) else ""
            self.var_detalhe_alvo.set(
                f"Alvo: {self.titulo_alvo}\nControle que vai receber o clique: {classe}{aviso}")
        except (ValueError, winapi.WinApiError) as erro:
            self.var_detalhe_alvo.set(f"Alvo: {self.titulo_alvo}\n({erro})")

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
        self._definir_status(engine.MODE_LABELS[ajustes.mode] + " rodando", "#15803d")
        self._atualizar_habilitados()

    def parar(self) -> None:
        if self.motor.running:
            self.motor.stop(wait=False)

    def alternar(self) -> None:
        self.parar() if self.motor.running else self.iniciar()

    def _testar_clique(self) -> None:
        try:
            engine.single_click(self._coletar_configuracao())
            self._definir_status("Clique de teste enviado", "#15803d")
        except (ValueError, winapi.WinApiError) as erro:
            messagebox.showerror("Auto Clicker", str(erro), parent=self.root)

    # ------------------------------------------------------------------
    # Comunicação com as outras threads (tudo passa por uma fila)
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
                    if erro:
                        self._definir_status("Erro", "#b91c1c")
                        messagebox.showerror("Auto Clicker", erro, parent=self.root)
                    elif motivo == "limite":
                        self._definir_status("Terminou (limite de cliques)", "#333")
                    else:
                        self._definir_status("Parado", "#333")
                    self._atualizar_habilitados()
                elif evento[0] == "aviso":
                    self._definir_status(evento[1], "#b45309")
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
            self._definir_status("Os dois atalhos não podem usar a mesma tecla", "#b45309")
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

    def _fechar(self) -> None:
        self.motor.stop()
        self.atalhos.stop()
        try:  # evita que a fila seja consultada depois da janela sumir
            self.root.after_cancel(self._agendamento)
        except (tk.TclError, AttributeError):
            pass
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
