# Auto Clicker

Macro de auto click para **Windows**, com interface em português e sem precisar
instalar nada além do Python. Ele faz três coisas:

| Modo | O que acontece |
|------|----------------|
| **Auto click** | Clica sem parar no intervalo que você escolher (ex.: 10 cliques por segundo). |
| **Segurar botão** | Aperta o botão do mouse e mantém pressionado até você mandar parar. |
| **Segurar + clique periódico** | Mantém o botão pressionado e, de tempos em tempos, solta e aperta de novo — ou seja, dá um clique sem largar de vez. |

Os cliques podem ser entregues de três formas:

| Onde clicar | Como funciona | O mouse fica livre? |
|-------------|---------------|---------------------|
| **Na posição atual do mouse** | O clique normal, onde o cursor estiver. | não |
| **Em uma janela, em segundo plano** | A mensagem de clique vai direto para a janela; o cursor não sai do lugar. | sim |
| **Em um ponto fixo da tela** | O mouse vai até o ponto, clica e volta sozinho para onde estava. | quase — ele pisca até o ponto a cada clique |

O modo em segundo plano é o único que deixa o mouse totalmente livre, mas ele
não funciona em jogos — veja a seção sobre isso mais abaixo.

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

## Transformar em .exe e instalar

Dê dois cliques em **`criar_exe.bat`**. Ele faz tudo sozinho:

1. procura o Python no computador;
2. baixa e instala o PyInstaller (só na primeira vez — precisa de internet);
3. desenha o ícone do programa (`ferramentas/gerar_icone.py`, sem usar nenhuma
   biblioteca de imagem);
4. gera um único arquivo: `dist\AutoClicker.exe`;
5. **mostra os discos do computador** (letra, nome e espaço livre) e pergunta
   em qual deles você quer instalar — C:, D:, um HD externo, o que estiver
   ligado;
6. pergunta o nome da pasta (padrão: `Auto Clicker`), copia o executável para
   lá e, se você quiser, cria um atalho na área de trabalho.

Se preferir não instalar na hora, é só responder `N`: o executável fica em
`dist\AutoClicker.exe` e você copia para onde quiser depois.

Sobre o `.exe` gerado:

- **não precisa de Python** na máquina onde ele vai rodar — dá para levar num
  pendrive;
- é um arquivo só, de uns 12 a 15 MB;
- como ele acabou de ser criado aí no seu computador, sem assinatura digital,
  o antivírus ou o SmartScreen pode perguntar se você confia na primeira
  execução. É só escolher "mais informações" e depois "executar assim mesmo".
  Auto clickers costumam ser marcados por heurística justamente por mexerem
  com mouse e teclado;
- se a pasta escolhida for protegida (a raiz de `C:`, por exemplo) e o Windows
  recusar, clique no `.bat` com o botão direito e use "Executar como
  administrador", ou escolha outra pasta.

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
- **Em uma janela, em segundo plano** — libera o seu mouse por completo. O
  clique é entregue direto para a janela alvo, sem mexer no cursor. Não
  funciona em jogos.
- **Em um ponto fixo da tela** — o mouse vai até o ponto, clica e volta na
  hora para onde estava. É o modo que funciona em jogos, com o jogo na frente.

Um desenho abaixo das opções mostra a diferença entre as três.

### Aba **Ponto** — qual janela e em que lugar

- Selecione a janela na lista (ela mostra o programa e o título), ou
- Passe o mouse por cima do ponto exato onde você quer clicar e aperte **F7**.
  O programa descobre sozinho qual é a janela e guarda a posição do ponto
  *dentro* dela — se a janela for movida depois, o clique continua caindo no
  lugar certo.

No modo **ponto fixo da tela** os campos X e Y são a posição na tela inteira, e
o F7 captura direto onde o cursor estiver — não é preciso escolher janela
nenhuma.

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

## Roblox, Minecraft e outros jogos

**O modo em segundo plano não funciona no Roblox** — e não é defeito do macro.
Jogos como Roblox, Minecraft, Fortnite e Valorant leem o mouse por *Raw Input*
/ DirectInput, ou seja, pegam o movimento e o clique direto do driver do
dispositivo. Mensagens de clique enviadas para a janela (que é o que o modo em
segundo plano faz) simplesmente não existem para eles. O Roblox ainda tem o
anti-cheat Hyperion, que bloqueia esse tipo de entrada de propósito.

O programa reconhece os jogos mais comuns pelo nome do executável e avisa na
tela antes de você perder tempo.

**O que funciona nesses jogos:**

1. Deixe o jogo **em janela** (não em tela cheia exclusiva) e **na frente**.
2. Escolha **"Em um ponto fixo da tela"** na aba Destino.
3. Na aba Ponto, passe o mouse no lugar que quer clicar e aperte **F7**.
4. Aumente a **duração de cada clique** para 50–80 ms: muitos jogos ignoram
   cliques curtos demais.
5. Aperte **F6** para começar. O cursor vai piscar até o ponto a cada clique e
   voltar sozinho.

Se o jogo estiver em primeira pessoa, com o mouse preso na câmera, use
**"Na posição atual do mouse"** — nesse caso o clique cai onde a mira estiver.

Vale saber: automatizar cliques vai contra as regras de uso de vários jogos,
Roblox incluído, e alguns detectam macros. A decisão de usar é sua, mas o
risco de punição na conta existe e não tem como o programa evitar isso.

## Quando o clique em segundo plano não funciona

Fora dos jogos, o clique em segundo plano é entregue como uma mensagem do
Windows (`PostMessage`) para a janela. A maioria dos programas de desktop e
navegadores aceita, mas ainda existem casos que não:

- **Programas abertos como administrador** só aceitam mensagens de outro
  programa também administrador. Se o alvo roda elevado, abra o Auto Clicker
  como administrador (botão direito → "Executar como administrador").
- **Janelas minimizadas** muitas vezes ignoram o clique — o programa avisa
  antes de começar. Deixe a janela aberta atrás das outras em vez de
  minimizada.
- **Alguns programas** só reagem ao mouse de verdade, mesmo não sendo jogos.

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
criar_exe.bat      gera o .exe e instala no disco que você escolher
iniciar.bat        roda direto pelo Python, sem gerar executável
auto_clicker.py    ponto de entrada usado pelo .exe
autoclicker/
  winapi.py    ligações com a API do Windows (SendInput, PostMessage, janelas)
  engine.py    motor de cliques: os três modos, rodando em uma thread
  hotkeys.py   atalhos globais de teclado
  config.py    salvar/carregar preferências
  tema.py      paleta, estilos e os elementos gráficos desenhados
  gui.py       interface em tkinter: as cinco abas e o rodapé
ferramentas/
  gerar_icone.py   desenha o ícone e escreve o .ico byte a byte
testes/
  test_engine.py   os três modos, o limite e a parada
  test_gui.py      montagem da janela, campos, atalhos e o ciclo completo
  test_icone.py    o formato do .ico e do .png gerados
```
