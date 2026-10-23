# Blender — assets 3D

Todos os modelos são gerados por script (Blender 5.2, headless), então dá para refazer qualquer um do zero. Rode da raiz do repositório, nesta ordem (o cenário importa os outros `.blend`):

```bash
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
"$BLENDER" -b --factory-startup -P blender/scripts/build_cup.py
"$BLENDER" -b --factory-startup -P blender/scripts/build_tutu.py
"$BLENDER" -b --factory-startup -P blender/scripts/build_gio.py
"$BLENDER" -b --factory-startup -P blender/scripts/build_desk.py
"$BLENDER" -b --factory-startup -P blender/scripts/bake_desk.py
"$BLENDER" -b --factory-startup -P blender/scripts/build_cup_fracture.py
```

| Script | Gera | Observações |
|---|---|---|
| `build_cup.py` | `cup.blend`, `public/models/cup.glb` | Caneca + superfície do café (`cup_coffee`) + âncora do vapor. Rótulo em textura: `textures/cup_label_en.png` / `cup_label_pt.png`. |
| `build_tutu.py` | `tutu.blend`, `public/models/tutu.glb` | Corpo único com pelagem em vertex color e rig `tutu_rig` (coluna, cabeça, orelhas, 4 patas, cauda em 5 ossos) com pesos automáticos; olhos, nariz e bigodes presos ao osso `head`, orelhas aos ossos `ear.*`. Poses em `pose(rig, nome)`: `sit`, `sit_bored`, `look_gio`, `look_cup`, `slap_raise`, `slap_hit`, `lean_cup`, `crouch`, `leap`, `land`, `innocent`, `picked_up`, `lap`. Animações no GLB: `tutu_lean_cup` (cena 0, espiando o café), `tutu_sit_bored_loop`, `tutu_look_gio`, `tutu_look_cup`, `tutu_slap`, `tutu_jump_down` (o site move a Tutu no arco da bancada ao chão entre os quadros 12 e 26), `tutu_sit_floor_innocent` ("não fui eu", com a gotinha de suor `tutu_sweat`), `tutu_picked_up` e `tutu_lap_loop`. Sentada, as patas da frente ganham escala no osso `front_upper.*` para alcançar o chão. |
| `build_gio.py` | `gio.blend`, `public/models/gio.glb` | Rig `gio_rig` com osso `root` (deslocamento/giro) e dedos; segmentos rígidos estilo action figure (cada peça 100% num osso). Óculos em objeto separado (`gio_glasses`). Animações em `gio_anim.py` (IK de braços e pernas, 24 fps): `gio_typing_loop`, `gio_mouse_loop`, `gio_broom_enter` (entra pela direita varrendo e para ao lado dos cacos), `gio_crouch_pick_cat` (solta a vassoura, agacha, pega a Tutu e levanta abraçada), `gio_sit_with_cat` (volta, vira de frente para a câmera e senta com a Tutu no colo) e `gio_idle_lap_loop`. Todas assumem o `gio_rig` na posição do empty `spot_gio_seat` girado 180°. Nós extras animados juntos: `gio_broom` (escala 0 quando não está em uso) e `gio_cat_anchor` (onde fica a raiz da Tutu; o site prende a Tutu nele durante o colo). Em `gio_sit_with_cat` ela senta de frente para a câmera: o site deve girar o nó `chair` do cenário 180° junto. |
| `build_desk.py` | `desk_scene.blend` | Ambiente estático (chão, parede, janela, bancada, monitor, teclado, mouse, post-its, luminária, cadeira) + empties `spot_*` para posicionar personagens e câmera, e a luz noturna (`night_lights`). O `.blend` também tem as personagens, só para os previews. |
| `bake_desk.py` | `desk_baked.blend`, `public/models/desk_scene.glb`, `textures/lightmap_*.png` | **Bake** (Cycles, CPU, ~23 min) da luz noturna + AO. Junta o ambiente em 4 grupos (`baked_floor`, `baked_room`, `baked_desk`, `chair` — a cadeira separada porque gira na cena 6), cria UV de lightmap e grava uma textura por grupo = cor (nítida) × iluminação difusa (suavizada para tirar o ruído) × AO + emissão. O site desenha esses grupos sem iluminação; `monitor_screen` fica fora do bake (o código rola). Rode depois de `build_desk.py`. |
| `build_cup_fracture.py` | `cup_fracture.blend`, `public/models/cup_fracture.glb` | Caneca cortada em células de Voronoi: `shard_01…05` (um por projeto de `projects.ts`, 17–27 cm³ cada; `shard_01` fica com "WORLD'S BEST", `shard_02` com "DEV", `shard_03` com a alça, `shard_05` é o pé) + `fragment_01…06` decorativos. Animação única `cup_fall_break` a 60 fps, em coordenadas do `desk_scene` (o quadro 1 coincide com a caneca inteira do cenário): quadros 1–14 o tapa empurra a caneca até a borda, 15–35 queda, **36 impacto** (`impact_frame` no empty `cup_fracture`), corpo rígido assado até o quadro 200. Inclui `cup_coffee` (some no impacto), `coffee_puddle` e `coffee_drop_01…14`. É determinístico: mesmo script = mesmos lugares. |

Convenções: 1 unidade = 1 m, Z para cima no Blender (o exportador converte para +Y no three.js), nomes em inglês `snake_case`, GLB com Draco e texturas WebP. Previews em `previews/`.

Pendências (fases seguintes da spec): nenhuma de modelagem/animação — a cena 0 é feita em CSS + shader no site, sem `loader_cup.blend`.
