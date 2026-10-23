# Gio Marcondes Portfólio — Especificação para o Claude Code

> Documento de referência do projeto. Leia inteiro antes de começar e consulte-o a cada fase.
> Sugestão: salvar na raiz do repositório como `CLAUDE.md` (ou referenciá-lo a partir dele).

---

## 0. Antes de qualquer coisa

1. **Leia as referências visuais** em `C:\Users\gica_\develop\personal\portifolio\docs`. Analise todas as imagens e escreva um resumo curto do estilo (formas, proporções, paleta, materiais, iluminação) em `docs/STYLE_NOTES.md` **antes de modelar qualquer coisa**. As fotos `eu_e_tutu` e `20260430_074912` são as referências principais da aparência da Giovanna e da gata Tutu. A `eu_e_tutu` também é a foto final do site (seção 8).
2. **Verifique a conexão com o Blender (MCP)**: rode `claude mcp list` e confirme que o servidor do Blender aparece como conectado. Faça um teste simples (ex.: listar objetos da cena padrão). Se não estiver conectado, pare e avise a Giovanna antes de continuar.
3. **Trabalhe por fases** (seção 12). Ao fim de cada fase, rode o projeto, mostre o resultado e espere aprovação antes de seguir.

---

## 1. Visão geral

Portfólio pessoal narrativo em 3D, guiado pelo scroll. Inspirações: a experiência 3D de bruno-simon.com e o acabamento visual (tipografia grande, revelações suaves, rolagem fluida) de landonorris.com. **Não copiar assets, código ou layouts desses sites** — são só referência de sensação.

**Tom:** divertido, fofo e aconchegante. Cena noturna, luz quente de luminária, brilho do monitor, vapor do café.

**História em uma frase:** a gata Tutu, curiosa com o café, derruba a xícara; cada caco é um projeto; a Giovanna chega com a vassoura, pega a Tutu no colo e se apresenta.

**Requisitos gerais**
- Bilíngue: português (padrão) e inglês, com seletor visível o tempo todo.
- **Sem som.**
- Toda a animação é **reversível**: rolar para cima "volta no tempo" (a xícara se recompõe, a Tutu volta para a bancada etc.).
- Desktop e mobile (scroll por roda, trackpad e toque).

---

## 2. Stack

| Camada | Escolha |
|---|---|
| Build | Vite + React + TypeScript |
| 3D | three.js via `@react-three/fiber` + `@react-three/drei` |
| Pós-processamento | `@react-three/postprocessing` (bloom suave, vinheta, DOF leve, grão sutil) |
| Scroll | Lenis (rolagem suave) + GSAP ScrollTrigger (timeline com `scrub`) |
| i18n | dicionários JSON (`/src/i18n/pt.json`, `/src/i18n/en.json`) + contexto React; idioma salvo em `localStorage` e detectado por `navigator.language` na primeira visita |
| Assets 3D | Blender → GLB com compressão Draco, texturas em KTX2/WebP, iluminação **assada (baked)** |
| Hospedagem | GitHub Pages (`marcondesgio.github.io`), deploy por GitHub Actions a cada push na `main` |
| Repositório | GitHub pessoal `marcondesgio` (sugestão de nome: `portfolio`) |

Use versões estáveis e fixas das dependências.

---

## 3. Princípio técnico central: tudo dirigido pelo progresso do scroll

- Existe **um único valor de progresso** `p ∈ [0, 1]` derivado do scroll.
- Câmera, animações dos personagens, queda e quebra da xícara e overlays de UI são **funções de `p`**. Nada roda "por conta própria" com tempo real, exceto loops ambientes (vapor, piscar de olhos, cauda balançando, tela do monitor).
- Animações vindas do Blender são tocadas com `AnimationMixer`, controlando o tempo manualmente (`action.time = f(p)`), nunca com `play()` livre. Isso garante a reversibilidade.
- **A quebra da xícara é pré-calculada no Blender** (fratura + simulação de corpo rígido assada em keyframes) e exportada como animação. Nada de física em tempo real: o resultado tem que ser determinístico e reversível, e os cacos principais precisam cair sempre nos mesmos lugares.
- A câmera segue um caminho definido por keyframes (posição + alvo) interpolados por `p`, com easing suave entre cenas.

---

## 4. Roteiro de cenas (timeline do scroll)

As faixas de `p` são ponto de partida; ajuste para o ritmo ficar bom.

### Cena 0 — Loading (antes do scroll existir)
- Tela cheia: **xícara vista de cima**, café escuro com reflexo dos **olhos da Tutu** (azul-claros).
- Loop dos olhos: **piscam → olham para a direita → olham para a esquerda → repete**.
- Vapor subindo do café.
- **Esta cena precisa ser leve e aparecer quase instantaneamente**: superfície do café como plano com shader (reflexo + leve ondulação), olhos como textura/SVG animado projetado no café, xícara simples. Meta: < 300 KB.
- Enquanto isso, a cena completa carrega em segundo plano (progresso real via `useProgress` ou `LoadingManager`). Um indicador discreto de porcentagem pode aparecer.
- Quando tudo estiver carregado, **espere terminar o ciclo atual dos olhos** e só então libere o scroll, com uma dica sutil ("role para baixo" / "scroll down" — no mobile, "deslize").
- Narrativa: a Tutu está debruçada sobre a xícara, por isso os olhos aparecem refletidos.

### Cena 1 — A bancada (p 0.00 → 0.15)
- A câmera sai da vista de cima e recua até um plano mais aberto e levemente lateral, revelando a bancada.
- A Tutu se afasta da xícara e senta ao lado dela, entediada mas curiosa.
- Composição da esquerda para a direita: **Giovanna de costas** (mão no mouse, digitando) → **Tutu** → **xícara**.
- Loops ambientes: digitação, mão no mouse, cauda da Tutu, orelhas mexendo, código rolando no monitor, vapor.

### Cena 2 — O tapa (p 0.15 → 0.30)
- A Tutu olha em direção à Giovanna (que não percebe), depois volta a olhar para a xícara e **dá um tapa** nela.
- A câmera se aproxima levemente da Tutu e da xícara.

### Cena 3 — A queda (p 0.30 → 0.45)
- A câmera **acompanha a perspectiva da queda** da xícara até o chão de madeira (pode girar em volta da xícara durante a queda para dar drama).
- O café espirra em gotas estilizadas (fofas, não realistas).
- Ao tocar o chão, **a xícara quebra**: no mínimo **5 cacos principais** + alguns fragmentos pequenos decorativos.

### Cena 4 — Os cacos são os projetos (p 0.45 → 0.65)
- Os 5 cacos principais ficam em destaque (leve brilho na borda, pequena flutuação).
- Esta faixa tem uma "zona de pausa": o scroll anda mais devagar aqui para dar tempo de interagir.
- **Desktop:** passar o mouse num caco mostra um **rótulo flutuante** com nome + descrição curta; o cursor vira "mão"; clicar abre o link em **nova aba** (`target="_blank" rel="noopener noreferrer"`).
- **Mobile:** primeiro toque mostra o rótulo; segundo toque no mesmo caco abre o link.
- Cacos "Em breve": mostram o rótulo "Em breve" / "Coming soon", sem clique e com cursor padrão.
- Os cacos são **gerados a partir de dados** (seção 7), para facilitar adicionar projetos depois. Se houver mais projetos que cacos, crie mais cacos principais no Blender.
- Acessibilidade: manter uma lista HTML acessível (navegável por teclado, legível por leitores de tela) com os mesmos links, sincronizada visualmente com o foco do caco.

### Cena 5 — A vassoura (p 0.65 → 0.80)
- Zoom out mantendo a **câmera baixa, quase no nível do chão**.
- Entram em cena **apenas as pernas e os pés da Giovanna** (calça jeans, tênis estilo skate old school preto e branco, **sem logo de marca**), um pedaço do cabo da vassoura e a vassoura.
- A Tutu está sentada no chão ao lado dos cacos, com cara de "não fui eu".
- A partir daqui os cacos viram cenário (não clicáveis).

### Cena 6 — Tutu no colo (p 0.80 → 0.92)
- A Giovanna se abaixa, pega a Tutu do chão e a coloca no colo (sentando de novo na cadeira).
- A câmera sobe até enquadrar o **torso da Giovanna com a Tutu no colo**.

### Cena 7 — Sobre mim (p 0.92 → 1.00)
- O personagem 3D com a Tutu **se dissolve** (transição com leve brilho) na **foto real** da Giovanna com a Tutu, mantendo o mesmo enquadramento.
- Ao lado, a seção **Sobre mim** (seção 8) com trajetória, formação, idiomas e contatos. Tipografia grande no estilo editorial do site de inspiração, com revelações suaves por linha.

### Reversão
Rolando para cima, tudo volta exatamente pelo mesmo caminho. Teste especialmente: foto → 3D, Tutu voltando do colo para o chão, xícara se recompondo e subindo de volta à bancada.

---

## 5. Personagens

### Giovanna (personagem principal, quase sempre de costas)
- Referência: fotos `eu_e_tutu` e `20260430_074912` e demais imagens da pasta `docs`, adaptadas ao estilo fofo/estilizado.
- **Cabelo:** ondulado, castanho-claro, na altura dos ombros, **solto**.
- **Roupa:** camiseta preta, calça jeans, tênis estilo skate old school preto e branco (sem logo).
- **Piercings:** argola na aba **esquerda** do nariz e piercing no **septo**. Aparecem só se o rosto ficar visível (ex.: cena 6 de perfil).
- Tom de pele e proporções: seguir as fotos de referência.
- Rig simples: braços, mãos com dedos (digitação e mouse), tronco, pernas (agachar, sentar).
- Animações necessárias: `gio_typing_loop`, `gio_mouse_loop`, `gio_broom_enter`, `gio_crouch_pick_cat`, `gio_sit_with_cat`, `gio_idle_lap_loop`.

### Tutu (Trufa) — gata
- Fêmea, **branca com manchas marrons**, **olhos azul-claros**. Seguir a pelagem das fotos de referência para as manchas ficarem parecidas.
- Estilo fofo: cabeça um pouco maior, olhos expressivos.
- Animações: `tutu_lean_cup` (loading), `tutu_sit_bored_loop` (cauda e orelhas), `tutu_look_gio`, `tutu_look_cup`, `tutu_slap`, `tutu_jump_down`, `tutu_sit_floor_innocent`, `tutu_picked_up`, `tutu_lap_loop`.
- Os olhos refletidos no café (cena 0) usam a mesma cor e formato dos olhos do modelo.

---

## 6. Ambiente e objetos

- **Hora:** noite. Ambiente aconchegante.
- **Iluminação:** luminária de mesa com luz quente (principal), brilho azulado/frio do monitor (contraluz), luz ambiente bem baixa. Assar no Blender e complementar com poucas luzes em tempo real só onde necessário.
- **Bancada:** branca.
- **Chão:** madeira, sem tapete.
- **Na bancada:** monitor, teclado, mouse, mouse pad, post-its coloridos (podem ter rabiscos fofos ou trechos de código), luminária, xícara.
- **Monitor:** editor de código com **tema escuro**, linhas de código rolando devagar (textura animada ou canvas). Pode mostrar código Dart/Flutter.
- **Cadeira** de trabalho (aparece de leve; importante na cena 6).
- **Xícara:** caneca branca com o texto **"WORLD'S BEST DEV"** em preto, numa fonte serifada bold arredondada, no estilo das canecas de presente clássicas. Opcional: trocar para "MELHOR DEV DO MUNDO" quando o site estiver em português (duas texturas). O texto precisa continuar legível nos cacos.
- **Vapor** do café: shader de fumaça suave em loop.
- Opcional: janela ao fundo com céu noturno desfocado e alguma planta, se ajudar a composição.

---

## 7. Projetos (dados dos cacos)

Arquivo `src/data/projects.ts`. Ordem dos cacos = ordem do array.

```ts
export const projects = [
  {
    id: 'ceramic-relax',
    name: 'Ceramic Relax',
    url: 'https://github.com/marcondesgio/ceramic-relax',
    description: {
      pt: 'Jogo 3D relaxante de cerâmica no navegador: modele no torno, pinte e leve ao forno.',
      en: 'A relaxing 3D pottery game in the browser: shape it on the wheel, paint it and fire it in the kiln.',
    },
  },
  {
    id: 'pode-comer',
    name: 'Pode Comer?',
    url: 'https://github.com/marcondesgio/podecomer-app',
    description: {
      pt: 'App em Flutter que lê o código de barras dos alimentos e alerta sobre alergênicos para cada pessoa da família.',
      en: 'A Flutter app that scans food barcodes and flags allergens for each member of the family.',
    },
  },
  {
    id: 'duni-app',
    name: 'Duni App',
    url: 'https://github.com/marcondesgio/duni_app',
    description: {
      pt: 'TODO: descrição curta (Giovanna vai enviar).',
      en: 'TODO: short description.',
    },
  },
  { id: 'soon-1', comingSoon: true },
  { id: 'soon-2', comingSoon: true },
];
```

Rótulo "Em breve": `pt: "Em breve"`, `en: "Coming soon"`.

---

## 8. Conteúdo — seção "Sobre mim"

### Identidade
- Nome do site: **Gio Marcondes Portfólio** (pt) / **Gio Marcondes Portfolio** (en).
- `<title>` e meta tags nos dois idiomas; imagem de Open Graph gerada a partir da cena da bancada.

### Texto (PT)
**Desenvolvedora Frontend**

Desenvolvedora Frontend com mais de 8 anos de experiência em tecnologia e mais de 4 anos atuando com desenvolvimento Flutter, aplicações web e mobile e soluções para o setor fintech.

Minha experiência inclui desenvolvimento de aplicações utilizando Flutter/Dart, construção de aplicações mobile e web, integração com APIs REST e serviços externos, além da utilização de arquitetura em camadas baseada em MVVM e práticas de Clean Code. Também possuo experiência com Angular, atividades de suporte backend, integração com Firebase, bancos NoSQL e utilização de pacotes e bibliotecas do ecossistema Flutter.

Ao longo da minha trajetória atuei em todo o ciclo de desenvolvimento de software, incluindo levantamento de requisitos, discussões técnicas, reuniões com clientes, planejamento de sprints, colaboração com equipes de Design e QA, documentação técnica e entrega de produtos.

Atualmente atuo em projetos do setor fintech, trabalhando com integrações e fluxos relacionados ao ecossistema Matera e serviços do mercado financeiro brasileiro. Anteriormente atuei na IBM em projetos para a TIM Brasil, fortalecendo minha experiência em qualidade de software, ambientes corporativos e estratégias de testes utilizando SIEBEL, SQL, Unix e Jenkins.

**Formação acadêmica**
- Mineração de Dados Complexos – Extecamp / Unicamp (2022)
- Bacharelado em Engenharia de Computação – Universidade São Francisco (2016–2020)
- Técnico em Informática – E.T.E.C. Rosa Perrone Scavone (2015)

**Idiomas**
- Inglês: nível B2 (Upper Intermediate), em evolução contínua com foco em comunicação profissional e oportunidades internacionais.

### Text (EN) — revisar com a Giovanna antes de publicar
**Frontend Developer**

Frontend developer with over 8 years of experience in technology and more than 4 years working with Flutter development, web and mobile applications, and solutions for the fintech sector.

My experience includes building applications with Flutter/Dart, developing mobile and web apps, integrating REST APIs and external services, and applying a layered MVVM-based architecture and Clean Code practices. I also have experience with Angular, backend support, Firebase integration, NoSQL databases, and packages and libraries from the Flutter ecosystem.

Throughout my career I have worked across the entire software development lifecycle, including requirements gathering, technical discussions, client meetings, sprint planning, collaboration with Design and QA teams, technical documentation, and product delivery.

I currently work on fintech projects, handling integrations and flows related to the Matera ecosystem and Brazilian financial market services. Previously, I worked at IBM on projects for TIM Brasil, strengthening my experience in software quality, enterprise environments, and testing strategies using SIEBEL, SQL, Unix, and Jenkins.

**Education**
- Complex Data Mining – Extecamp / Unicamp (2022)
- B.Sc. in Computer Engineering – Universidade São Francisco (2016–2020)
- IT Technician – E.T.E.C. Rosa Perrone Scavone (2015)

**Languages**
- English: B2 (Upper Intermediate), continuously improving with a focus on professional communication and international opportunities.

### Contatos
- E-mail: `giomarcondesdev@gmail.com` (link `mailto:` + botão "copiar")
- LinkedIn: https://www.linkedin.com/in/marcondesgio/
- GitHub: https://github.com/marcondesgio

### Foto final
- Usar a imagem **`eu_e_tutu`** da pasta `docs`, sem alterações de conteúdo. Copie para `public/images/`, converta para WebP (com fallback JPG), gere tamanhos responsivos e otimize o peso (meta: < 250 KB na maior versão).
- Na cena 7, o enquadramento final da câmera na cena 6 deve imitar o enquadramento dessa foto (posição do torso e da Tutu), para o dissolve do 3D para a foto ficar natural.
- **Não edite nem gere o rosto, o corpo ou a roupa da foto por código.** Recorte e ajuste de cor leve são permitidos se necessário.

---

## 9. Direção visual e UI

- Paleta e tipografia: seguir o design system gerado no Claude Design (arquivo de prompts `CLAUDE_DESIGN_PROMPTS.md`). Ponto de partida, se ainda não houver:
  - Noite: `#1C1B2E` (fundo), `#2A2944` (superfícies)
  - Luz quente da luminária: `#F4B860`
  - Café: `#6B4A3A`
  - Creme/texto claro: `#F6EFE6`
  - Olhos da Tutu (acento): `#9FD3F0`
  - Acento fofo: `#F2A7A0`
  - Fontes: **Fraunces** (títulos grandes, um toque fofo), **DM Sans** (texto), **JetBrains Mono** (detalhes "dev": rótulos, porcentagem do loading)
- Efeitos inspirados no site de referência:
  - rolagem suave (Lenis)
  - títulos grandes com revelação por linha/palavra
  - cursor customizado discreto (vira "mão de patinha" sobre os cacos clicáveis — opcional)
  - transições com máscara
- UI fixa sobre o 3D: nome do site (canto superior esquerdo), seletor PT | EN (canto superior direito), indicador de progresso do scroll discreto.
- Ícones: Lucide ou SVG próprios.

---

## 10. Desempenho, acessibilidade e SEO

- **Orçamento:** cena 0 < 300 KB; cena completa < 8 MB (GLB Draco + KTX2). Meta de 60 fps em desktop médio e ≥ 30 fps em celular intermediário.
- Limitar `dpr` (máx. 2; 1.5 no mobile). Pós-processamento reduzido no mobile.
- Detectar GPU fraca (ex.: `detect-gpu`) e `prefers-reduced-motion`. Nesses casos, ou se WebGL falhar, mostrar a **versão simplificada**: página estática bonita com uma imagem da cena, lista de projetos, seção Sobre e contatos.
- Conteúdo textual (projetos, sobre, contatos) presente no HTML, não só no canvas, para o Google indexar.
- Contraste adequado, navegação por teclado, `aria-label` nos controles, `lang` atualizado ao trocar de idioma.

---

## 11. Fluxo no Blender (via MCP)

- Um arquivo `.blend` por grupo: `loader_cup.blend`, `desk_scene.blend`, `gio.blend`, `tutu.blend`, `cup_fracture.blend`. Guardar em `/blender` no repositório (avaliar Git LFS se ficarem grandes).
- Estilo low-poly/estilizado, formas arredondadas, materiais simples, de acordo com `docs/STYLE_NOTES.md`.
- **Xícara:** modelar inteira, aplicar fratura (Cell Fracture) gerando os 5+ cacos principais com tamanhos parecidos e alguns fragmentos pequenos; simular corpo rígido no chão de madeira; **assar a simulação em keyframes**; nomear os cacos `shard_01`… `shard_05` na ordem de `projects.ts`.
- **Bake** de iluminação e AO nas texturas dos objetos estáticos.
- Nomes de objetos e animações em inglês, `snake_case`, conforme listas da seção 5.
- Exportar GLB (Draco), conferir escala (1 unidade = 1 metro) e orientação (+Y para cima no three.js).
- Antes de exportar cada personagem, gerar um render de prévia (frente, lado, costas) e mostrar para aprovação.

---

## 12. Fases de entrega

1. **Setup:** repositório, Vite + R3F, Lenis + ScrollTrigger com `p` global, i18n, deploy inicial na Vercel.
2. **Estilo:** `STYLE_NOTES.md` + design system (do Claude Design) aplicado em tokens CSS.
3. **Cena 0 (loading)** completa e leve.
4. **Bancada** (ambiente, luz noturna, objetos) + caminho de câmera da cena 1, com placeholders para personagens.
5. **Tutu** modelada, rigada e animada (cenas 0–2 e 5–6).
6. **Xícara fraturada** + cenas 3–4 com interação dos cacos.
7. **Giovanna** modelada, rigada e animada (cenas 1, 5, 6).
8. **Cena 7** (dissolve para a foto + Sobre mim).
9. **Polimento:** pós-processamento, versão simplificada, mobile, SEO, acessibilidade, testes de reversão.
10. **Publicação** final na Vercel.

---

## 13. Pendências da Giovanna

- [ ] Descrição curta do **Duni App** (pt/en).
- [ ] Revisar a tradução em inglês da seção Sobre.
- [ ] Decidir se a caneca troca o texto para português no modo PT.
