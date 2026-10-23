# Gio Marcondes Portfólio

Portfólio narrativo em 3D guiado pelo scroll. Especificação: [docs/PORTFOLIO_SPEC.md](docs/PORTFOLIO_SPEC.md). Assets 3D: [blender/README.md](blender/README.md).

```bash
npm install
npm run dev        # http://localhost:5173 — adicione ?debug para o painel de p e de clipes
npm run build      # typecheck + build de produção em dist/
npm test           # testes de reversão da linha do tempo (vitest)
```

## Como está organizado

- `src/loader/` — **cena 0** (loading), no bundle inicial (~78 KB gzip com React; meta < 300 KB): caneca vista de cima em CSS, café num fragment shader WebGL puro (`CoffeeSurface`, sem three.js), olhos da Tutu em SVG com o loop em CSS (pisca → direita → esquerda, `EYE_CYCLE_MS`) e vapor. Mostra o progresso real (`loadState`); quando tudo carrega, espera o fim do ciclo dos olhos para liberar o scroll. Ao rolar, faz fade sobre a caneca 3D, que a câmera enquadra igual em p = 0 (mesma fórmula de tamanho em `loader.css` e `CameraRig`).
- `src/shards/` — **cena 4**, os cacos como projetos (`shard_01…05` ↔ ordem de `src/data/projects.ts`). `ShardFx` dá brilho de borda (fresnel) e flutuação no shader e calcula a posição na tela; `shardStore` guarda o caco ativo e é compartilhado por hover/clique (desktop), dois toques (mobile), o rótulo flutuante (`ShardLabel`, variantes do design system, "Em breve" sem link) e a lista HTML acessível (`ProjectList`, aparece ao receber foco do teclado e leva a história à cena 4). Interativo entre p 0,49 e 0,65; essa faixa ocupa 2,4× mais scroll (zona de pausa em `scroll/progress.ts`).
- `src/about/` — **cena 7**, "Sobre mim" (design system pp. 10–12). `About` fica no fluxo normal logo depois da trilha da história (sobrepõe a última tela, então em p = 1 está no topo) e só reserva o lugar da foto; `PhotoDissolve` é a foto fixa: dissolve com brilho sobre o 3D no mesmo enquadramento (p 0,915–0,95), desliza até o lugar reservado (0,955–0,995) enquanto um véu noturno cobre o 3D, e depois acompanha o lugar. Foto gerada por `npm run photo` (`scripts/optimize-photo.mjs`: WebP + JPG em 480/768/1024 px, maior = 139 KB).
- `src/lite/` — **versão simplificada** (design system pp. 13–15): página estática com imagem da cena, cards dos projetos, Sobre e contatos. Entra com "reduzir movimento", sem WebGL, GPU por software/muito fraca ou pouca memória (`mode.ts`), ou se a história 3D der erro (`StoryBoundary` em `App.tsx`). Force com `?lite` ou `?full`.
- `src/scene/Effects.tsx` — pós-processamento: bloom suave, vinheta, profundidade de campo leve (foco no alvo da câmera) e grão; no celular sem DOF e sem MSAA.
- **SEO**: `index.html` tem canonical, Open Graph/Twitter (`public/og.jpg`, gerada por `npm run scene-images`), JSON-LD de Person e um `<noscript>` com o conteúdo; `public/robots.txt` e `sitemap.xml`. A URL pública vem de `VITE_SITE_URL` (padrão `https://marcondesgio.github.io` em `vite.config.ts`).
- **Deploy**: GitHub Pages via Actions (`.github/workflows/deploy.yml`) — cada push na `main` roda testes, build e publica `dist/` em https://marcondesgio.github.io.
- **Reversão**: `npm test` verifica que `storyAt(p)` é idêntico indo e voltando, contínuo e só usa clipes que existem nos GLBs; com `?debug`, o botão *reversal test* percorre a história no navegador e compara câmera, Tutu, Gio, cacos e cadeira indo e voltando (deixe a aba visível — o navegador pausa o 3D em aba oculta).
- `src/scene/Heavy.tsx` — o pedaço carregado sob demanda (three.js, R3F, drei, GSAP, Lenis e os GLBs).

- `src/scroll/` — Lenis + um ScrollTrigger sobre uma trilha alta; o progresso dele é o **p ∈ [0, 1]** global (`progress.ts`), lido a cada frame pela cena sem re-render. As faixas das cenas ficam em `SCENES`.
- `src/scene/timeline.ts` — função pura `storyAt(p)`: qual clipe cada personagem toca e em que ponto. Rolar para cima é só avaliar um p menor.
- `src/scene/ClipPlayer.ts` — toca os clipes assados no Blender com `action.time` definido à mão (nunca `play()` livre); loops ambientes usam o relógio.
- `src/scene/Story.tsx` — carrega os GLBs de `public/models/` (Draco local em `public/draco/`), posiciona tudo pelos empties `spot_*` do cenário e prende a Tutu ao `gio_cat_anchor` quando a Gio a carrega.
- `src/scene/CameraRig.tsx` — caminho de câmera por keyframes em p, interpolado por spline Catmull-Rom (keys repetidas = pausa); na cena 3 orbita a caneca caindo (`focus.ts`), e há um parallax leve com o mouse.
- `src/scene/Lights.tsx` — o ambiente vem com luz e AO assados (`blender/scripts/bake_desk.py`) e é desenhado sem iluminação; em tempo real só a luminária e o monitor (+ uma luz ambiente fraca para os personagens).
- `src/i18n/` — `pt.json` / `en.json` + contexto; idioma salvo em `localStorage`, detectado por `navigator.language`, `<html lang>` e `<title>` atualizados.
- `src/styles/tokens.css` — tokens do design system (cores, tipos, espaços, raios, sombras, glows, movimento).
