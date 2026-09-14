# Auto Clicker

Macro de auto click para **Windows**, com interface em português e sem precisar
instalar nada além do Python. Ele faz três coisas:

| Modo | O que acontece |
|------|----------------|
| **Auto click** | Clica sem parar no intervalo que você escolher (ex.: 10 cliques por segundo). |
| **Segurar botão** | Aperta o botão do mouse e mantém pressionado até você mandar parar. |
| **Segurar + clique periódico** | Mantém o botão pressionado e, de tempos em tempos, solta e aperta de novo — ou seja, dá um clique sem largar de vez. |

E, o mais importante: os cliques podem ir **direto para uma janela específica,
em segundo plano**. O cursor não sai do lugar, então você continua usando o
mouse normalmente enquanto o macro clica na outra janela.

## Como rodar

1. Instale o [Python 3.10 ou mais novo](https://www.python.org/downloads/windows/)
   (marque "Add Python to PATH" durante a instalação).
2. Baixe esta pasta.
3. Dê dois cliques em **`iniciar.bat`**.

Se preferir o terminal:

```cmd
python -m autoclicker
```

Não existem dependências externas: só a biblioteca padrão do Python
(`tkinter` + `ctypes`), que já vem junto no instalador oficial do Windows.

## Como usar

### 1. O que o macro faz

Escolha o modo, o botão do mouse (esquerdo, direito ou meio) e os tempos:

- **Intervalo entre cliques** — em milissegundos; a tela mostra quantos cliques
  por segundo aquilo dá (100 ms ≈ 10 cliques/s).
- **Variação aleatória** — sorteia um pouco para mais ou para menos a cada
  clique, deixando o ritmo menos "robótico". 0% = sempre igual.
- **Clicar a cada** — usado no modo "segurar + clique periódico": de quanto em
  quanto tempo ele solta e aperta o botão de novo.
- **Duração de cada clique** — quanto tempo o botão fica apertado em cada
  clique. Alguns programas ignoram cliques rápidos demais; se for o seu caso,
  aumente para 50–80 ms.
- **Parar depois de N cliques** — deixe 0 para não ter limite.

### 2. Onde os cliques vão cair

- **Na posição atual do mouse** — o clique normal, igual a qualquer auto
  clicker: acontece onde o cursor estiver naquele momento.
- **Em uma janela escolhida, em segundo plano** — é a opção que libera o seu
  mouse. O clique é entregue direto para a janela alvo, sem mexer no cursor.

Para escolher a janela e o ponto:

- Selecione a janela na lista (ela mostra o programa e o título), ou
- Passe o mouse por cima do ponto exato onde você quer clicar e aperte **F7**.
  O programa descobre sozinho qual é a janela e guarda a posição do ponto
  *dentro* dela — se a janela for movida depois, o clique continua caindo no
  lugar certo.

Os campos **X** e **Y** aceitam ajuste manual, "Usar o centro da janela"
preenche o meio da área útil, e **"Testar 1 clique"** manda um único clique
para conferir se a janela alvo aceita o comando antes de deixar o macro solto.

Logo abaixo aparece o controle interno que vai receber o clique (por exemplo
`Chrome_RenderWidgetHostHWND`) — é a confirmação de que o alvo foi encontrado.

### 3. Atalhos do teclado

- **F6** — inicia e para (funciona mesmo com o jogo ou o navegador em primeiro
  plano; é assim que você para o modo "segurar" sem ficar com o botão travado).
- **F7** — captura a janela e o ponto embaixo do cursor.

Dá para trocar as duas teclas nas caixas de seleção (F1–F12, Insert, Delete,
Home, End, Page Up/Down, Scroll Lock, Pause, `*`, `-` e `+` do teclado
numérico). Se alguma tecla já estiver sendo usada por outro programa, o
Auto Clicker avisa e você escolhe outra.

Suas preferências são salvas automaticamente ao fechar, em
`%APPDATA%\AutoClickerBR\config.json`.

## Quando o clique em segundo plano não funciona

O clique em segundo plano é entregue como uma mensagem do Windows
(`PostMessage`) para a janela. A maioria dos programas de desktop, navegadores
e jogos em janela aceita isso — mas nem todos:

- **Jogos que leem o mouse por DirectInput/Raw Input** (a maioria dos jogos de
  tiro e de ação, principalmente em tela cheia) ignoram mensagens e só
  respondem ao mouse de verdade. Nesses casos use o modo "na posição atual do
  mouse".
- **Jogos com anti-cheat** costumam bloquear (e podem punir) qualquer
  automação. Não use lá.
- **Programas abertos como administrador** só aceitam mensagens de outro
  programa também administrador. Se o alvo roda elevado, abra o Auto Clicker
  como administrador (botão direito no `iniciar.bat` → "Executar como
  administrador").
- **Janelas minimizadas** muitas vezes ignoram o clique — o programa avisa
  antes de começar. Deixe a janela aberta atrás das outras em vez de
  minimizada.

O botão "Testar 1 clique" existe justamente para você descobrir em qual desses
casos está, em dois segundos, sem precisar adivinhar.

## Rodando os testes

Os testes cobrem o motor de cliques (os três modos, o limite, a parada e a
garantia de que o botão nunca fica preso pressionado). Eles usam um dublê no
lugar do mouse, então rodam em qualquer sistema:

```cmd
python -m unittest discover -s testes -v
```

## Organização do código

```
autoclicker/
  winapi.py    ligações com a API do Windows (SendInput, PostMessage, janelas)
  engine.py    motor de cliques: os três modos, rodando em uma thread
  hotkeys.py   atalhos globais de teclado
  config.py    salvar/carregar preferências
  gui.py       interface em tkinter
testes/
  test_engine.py
```
