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

A janela é dividida em cinco abas, além do rodapé fixo com o botão de iniciar,
a luz de status e o contador de cliques.

### Aba **Modo** — o que o macro faz

As três opções aparecem como cartões; a escolhida fica destacada em azul bebê.
Aqui também ficam o botão do mouse (esquerdo, direito ou meio) e o campo
"Parar depois de N cliques" (0 = sem limite).

### Aba **Tempos** — o ritmo

- **Intervalo entre cliques** — em milissegundos. Logo abaixo, uma barra mostra
  onde o seu ritmo cai, de "devagar" até "muito rápido", com a marcação em
  cliques por segundo.
- **Variação aleatória** — sorteia um pouco para mais ou para menos a cada
  clique, deixando o ritmo menos "robótico". 0% = sempre igual.
- **Clicar a cada** — no modo "segurar + clique periódico", de quanto em quanto
  tempo ele solta e aperta o botão de novo.
- **Duração de cada clique** — quanto tempo o botão fica apertado. Alguns
  programas ignoram cliques rápidos demais; se for o seu caso, aumente para
  50–80 ms.

### Aba **Destino** — onde os cliques vão cair

- **Na posição atual do mouse** — o clique normal, igual a qualquer auto
  clicker: acontece onde o cursor estiver naquele momento.
- **Em uma janela, em segundo plano** — é a opção que libera o seu mouse. O
  clique é entregue direto para a janela alvo, sem mexer no cursor.

Um desenho ao lado das opções mostra a diferença entre as duas.

### Aba **Janela** — qual janela e em que ponto

- Selecione a janela na lista (ela mostra o programa e o título), ou
- Passe o mouse por cima do ponto exato onde você quer clicar e aperte **F7**.
  O programa descobre sozinho qual é a janela e guarda a posição do ponto
  *dentro* dela — se a janela for movida depois, o clique continua caindo no
  lugar certo.

Os campos **X** e **Y** aceitam ajuste manual, "Usar o centro da janela"
preenche o meio da área útil, e **"Testar 1 clique"** manda um único clique
para conferir se a janela alvo aceita o comando antes de deixar o macro solto.

Um mini mapa desenha a janela alvo em escala, com uma mira no ponto exato em
que o clique vai cair. Ao lado dos botões aparece o controle interno que vai
receber o clique (por exemplo `Chrome_RenderWidgetHostHWND`) — é a confirmação
de que o alvo foi encontrado.

### Aba **Atalhos**

- **F6** — inicia e para (funciona mesmo com o jogo ou o navegador em primeiro
  plano; é assim que você para o modo "segurar" sem ficar com o botão travado).
- **F7** — captura a janela e o ponto embaixo do cursor.

Dá para trocar as duas teclas nas caixas de seleção (F1–F12, Insert, Delete,
Home, End, Page Up/Down, Scroll Lock, Pause, `*`, `-` e `+` do teclado
numérico). Se alguma tecla já estiver sendo usada por outro programa, o
Auto Clicker avisa e você escolhe outra. Nesta aba também fica a opção de
manter a janela sempre visível.

Suas preferências são salvas automaticamente ao fechar, em
`%APPDATA%\AutoClickerBR\config.json`.

## Visual

O tema é **branco gelo com azul bebê**, e todos os elementos gráficos são
desenhados pelo próprio programa (Canvas do tkinter), sem imagens externas:

- cabeçalho com degradê, logo do mouse e ondas de clique que se animam
  enquanto o macro está rodando;
- cartões com ícones desenhados (mouse, relógio, alvo, janela, teclado);
- barra de ritmo em escala logarítmica na aba Tempos;
- desenho comparando clique no cursor x clique em segundo plano;
- mini mapa da janela alvo com a mira no ponto do clique;
- luz de status no rodapé (cinza parado, verde rodando, vermelho em erro);
- marca d'água **powered by nova era** no rodapé.

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
garantia de que o botão nunca fica preso pressionado) e a interface (montagem
da janela, campos que ligam e desligam conforme o modo, avisos de erro e o
ciclo iniciar/parar pelo atalho). Eles usam dublês no lugar do mouse e do
teclado, então rodam sem clicar nada:

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
  tema.py      paleta, estilos e os elementos gráficos desenhados
  gui.py       interface em tkinter: as cinco abas e o rodapé
testes/
  test_engine.py   os três modos, o limite e a parada
  test_gui.py      montagem da janela, campos, atalhos e o ciclo completo
```
