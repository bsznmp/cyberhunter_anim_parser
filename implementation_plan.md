# GUI com Viewport 3D

## Objetivo
Aplicação PyQt5 com viewport OpenGL 3D funcional, lista de arquivos .mesh, e exportação FBX.

## Dependências (todas instaladas ✅)
- PyQt5 + QtOpenGL
- ModernGL 5.12
- NumPy 2.4
- Pyrr 0.10

## Layout da Interface

```
┌─────────────────────────────────────────────┐
│  Menu: File │ Export                          │
│  Toolbar: [Load Folder] [Export FBX]         │
├──────────┬──────────────────────────────────┤
│ File List│                                   │
│          │         Viewport 3D               │
│ body.mesh│      (ModernGL + Shaders)         │
│ head.mesh│                                   │
│ hair.mesh│    Órbita: Mouse Drag             │
│ eye.mesh │    Zoom: Scroll                   │
│          │    Pan: Middle Mouse               │
├──────────┴──────────────────────────────────┤
│ Status: 15759 verts │ 23603 faces │ 114 bones│
└─────────────────────────────────────────────┘
```

## Proposed Changes

### GUI Core

#### [NEW] [app.py](file:///c:/Users/diesel/Desktop/_parser/app.py)
Entry point da aplicação GUI. `QMainWindow` com:
- Menu (Load Folder, Export FBX, Exit)
- Toolbar com botões
- Splitter horizontal: QListWidget (esquerda) + ViewerWidget (direita)
- Status bar com contagens do mesh

#### [NEW] [gui/viewer.py](file:///c:/Users/diesel/Desktop/_parser/gui/viewer.py)
`ViewerWidget(QOpenGLWidget)` — Widget OpenGL integrado ao PyQt5:
- Inicializa contexto ModernGL
- Mouse: órbita (left drag), pan (middle drag), zoom (scroll)
- Carrega mesh via `load_mesh(dto)` → cria VBO/IBO/VAO
- Render loop com shaders

#### [NEW] [gui/camera.py](file:///c:/Users/diesel/Desktop/_parser/gui/camera.py)
Classe Camera com matrizes view/projection:
- Projeção perspectiva (pyrr)
- Órbita esférica (azimuth + elevation + distance)
- Pan (translate target)

#### [NEW] [gui/shaders/mesh.vert](file:///c:/Users/diesel/Desktop/_parser/gui/shaders/mesh.vert)
Vertex shader: transforma posições e passa normais ao fragment.

#### [NEW] [gui/shaders/mesh.frag](file:///c:/Users/diesel/Desktop/_parser/gui/shaders/mesh.frag)
Fragment shader: iluminação diffuse + ambient simples usando normais.

#### [NEW] [gui/shaders/grid.vert](file:///c:/Users/diesel/Desktop/_parser/gui/shaders/grid.vert)
#### [NEW] [gui/shaders/grid.frag](file:///c:/Users/diesel/Desktop/_parser/gui/shaders/grid.frag)
Grid de chão para referência espacial.

---

## Fluxo de Interação

```
1. User clica "Load Folder" → QFileDialog
2. Lista popula com *.mesh da pasta selecionada
3. User clica num arquivo → parser.py:parse_mesh()
4. MeshDTO → ViewerWidget.load_mesh(dto)
   ├── Posições + Normais → VBO interleaved (-x, y, z para OpenGL)
   ├── Faces → IBO
   └── Render com iluminação
5. User clica "Export FBX" → Blender headless (mesmo pipeline do main.py)
```

## Verification Plan
- Rodar `python app.py` → janela abre com viewport escuro
- Load folder com lingzi → lista mostra os .mesh
- Clicar em lingzi.mesh → modelo aparece no viewport iluminado
- Orbitar com mouse → câmera funciona
- Export FBX → gera arquivo importável no Blender
