# Prompts para o Claude Design — Gio Marcondes Portfólio

Use na ordem. Anexe ao primeiro prompt as imagens de referência da pasta `docs` (estilo 3D e as fotos `eu_e_tutu` e `20260430_074912`) para o Claude Design seguir o mesmo clima. O resultado do prompt 1 deve ser reaproveitado nos seguintes.

---

## Prompt 1 — Identidade visual e design system

Crie o design system do site "Gio Marcondes Portfólio", um portfólio pessoal de desenvolvedora frontend apresentado como uma história 3D interativa: à noite, numa bancada de trabalho, a gata Tutu (branca com manchas marrons e olhos azul-claros) derruba uma caneca de café, os cacos viram os projetos, e no final a Giovanna aparece com a gata no colo.

O tom é divertido, fofo e aconchegante: noite, luz quente de luminária, brilho de monitor, vapor de café. O acabamento deve ser editorial e premium, com tipografia grande e muito espaço, sem parecer infantil.

Inclua:
- paleta para fundo noturno, com cores para luz quente, café, creme, um acento azul-claro inspirado nos olhos da Tutu e um acento rosado suave, com indicação de uso de cada cor e contraste acessível para texto;
- tipografia: uma display serifada com personalidade para títulos enormes, uma sans para texto e uma mono para detalhes "dev" (rótulos, porcentagens); todas do Google Fonts;
- escala tipográfica, espaçamentos, raios de borda, sombras e brilhos (glow);
- componentes: botão primário e secundário, link com ícone, seletor de idioma PT | EN, rótulo flutuante de projeto, indicador de progresso de scroll, dica "role para baixo", card de contato, item de formação acadêmica;
- estados de hover, foco e desativado.

Ponto de partida que pode ser refinado: fundo #1C1B2E, superfícies #2A2944, luz quente #F4B860, café #6B4A3A, creme #F6EFE6, acento #9FD3F0, rosado #F2A7A0; fontes Fraunces, DM Sans e JetBrains Mono.

---

## Prompt 2 — UI sobreposta à cena 3D (desktop e mobile)

Usando o design system do Gio Marcondes Portfólio, desenhe a interface que fica por cima de uma cena 3D em tela cheia, em desktop (1440px) e mobile (390px). A cena 3D ocupa todo o fundo; a UI deve ser mínima e não competir com ela.

Elementos:
- nome "Gio Marcondes Portfólio" no canto superior esquerdo;
- seletor de idioma PT | EN no canto superior direito;
- indicador de progresso de scroll discreto (linha fina ou pontinhos na lateral);
- tela de loading: a cena é uma caneca de café vista de cima com olhos de gato refletidos no café; desenhe só a sobreposição: porcentagem de carregamento em fonte mono e, quando completo, a dica "role para baixo" / "scroll down" (no mobile, "deslize para cima");
- rótulo flutuante de projeto que aparece ao passar o mouse sobre um caco da caneca: nome do projeto, descrição de uma linha e um pequeno indicativo "abre no GitHub ↗". Mostre três variações com estes conteúdos:
  - Ceramic Relax — "Jogo 3D relaxante de cerâmica no navegador: modele no torno, pinte e leve ao forno."
  - Pode Comer? — "App em Flutter que lê o código de barras dos alimentos e alerta sobre alergênicos para cada pessoa da família."
  - Em breve — estado sem link, mais apagado.
- versão mobile do rótulo, que aparece no primeiro toque, com a instrução "toque de novo para abrir".

---

## Prompt 3 — Seção "Sobre mim"

Usando o design system do Gio Marcondes Portfólio, desenhe a seção final "Sobre mim", em desktop e mobile. Do lado esquerdo (no mobile, em cima) fica uma foto real da Giovanna com a gata Tutu no colo, enquadrada da cintura para cima; use a foto `eu_e_tutu` anexada, respeitando a proporção dela. Do lado direito, o conteúdo em estilo editorial, com título grande e texto que será revelado linha a linha no scroll.

Conteúdo:
- Título: "Desenvolvedora Frontend"
- Resumo: "Desenvolvedora Frontend com mais de 8 anos de experiência em tecnologia e mais de 4 anos atuando com desenvolvimento Flutter, aplicações web e mobile e soluções para o setor fintech."
- Destaques de experiência (resuma visualmente, sem bloco de texto longo): Flutter/Dart, mobile e web, APIs REST, MVVM e Clean Code, Angular, Firebase, NoSQL; ciclo completo de desenvolvimento; fintech no ecossistema Matera; IBM em projetos para a TIM Brasil (qualidade de software, SIEBEL, SQL, Unix, Jenkins).
- Formação: Mineração de Dados Complexos – Extecamp / Unicamp (2022); Bacharelado em Engenharia de Computação – Universidade São Francisco (2016–2020); Técnico em Informática – E.T.E.C. Rosa Perrone Scavone (2015).
- Idiomas: Inglês B2 (Upper Intermediate).
- Contatos: e-mail giomarcondesdev@gmail.com (com botão de copiar), LinkedIn, GitHub.

Mostre também a versão em inglês do título e dos rótulos, para conferir que o layout aguenta textos de tamanhos diferentes.

---

## Prompt 4 — Versão simplificada (sem 3D)

Usando o design system do Gio Marcondes Portfólio, desenhe a versão simplificada do site, mostrada para quem usa "reduzir movimento" ou tem um aparelho sem suporte a 3D. É uma página única e estática, em desktop e mobile, com:
- topo com o nome do site, seletor PT | EN e uma ilustração estática da cena noturna (bancada branca, monitor com código em tema escuro, luminária, a gata Tutu e a caneca "WORLD'S BEST DEV") — reserve o espaço com placeholder;
- lista de projetos em cards (Ceramic Relax, Pode Comer?, Duni App e dois "Em breve"), cada um com link para o GitHub;
- a seção "Sobre mim" e os contatos.

Deve parecer parte da mesma marca, não uma página de erro.

---

## Prompt 5 (opcional) — Folhas de personagem para guiar o 3D

Crie duas folhas de referência de personagem no estilo fofo e estilizado das imagens anexadas, para guiar a modelagem 3D:

1. **Tutu (Trufa)** — gata fêmea, branca com manchas marrons (siga o padrão da foto anexada), olhos azul-claros, cabeça levemente maior, expressão entediada mas curiosa. Vistas de frente, lado e costas, mais três expressões: entediada, curiosa e "não fui eu".
2. **Giovanna** — cabelo ondulado castanho-claro na altura dos ombros, solto; camiseta preta, calça jeans, tênis estilo skate old school preto e branco sem logo; argola na aba esquerda do nariz e piercing no septo. Baseie o rosto e as proporções na foto anexada, no mesmo estilo fofo. Vistas de frente, lado e costas.

Fundo neutro, com a paleta do design system.
