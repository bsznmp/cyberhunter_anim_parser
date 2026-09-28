# CLAUDE.md

## Project Vision
A fast, modular viewer and converter for NeoX Engine assets, favoring reliability in binary parsing and high-performance 3D visualization.

## Technical Stack
- **Languages**: Python 3.10+, GLSL (Modern OpenGL 3.3+)
- **GUI**: PyQt5
- **3D Engine**: ModernGL, NumPy, Pyrr
- **Export**: Blender BPY (Headless)

## Conventions
### Naming
- **Files/Modules**: `snake_case` (e.g., `mesh_parser.py`)
- **Classes**: `PascalCase` (e.g., `MainWindow`, `ViewerWidget`)
- **Functions/Variables**: `snake_case` (e.g., `load_mesh`, `current_dto`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_BONES`)

### Architecture
- **core/**: Stateless binary parsers and DTO definitions.
- **gui/**: UI components and widget-to-renderer bridges.
- **runtime/**: Real-time calculation state (skinning, animation timeline).
- **export/**: External pipeline adapters (Blender scripts).

### Error Handling
- Use [core/exceptions.py](file:///c:/Users/diesel/Desktop/_parser/core/exceptions.py) as the base for all domain exceptions.
- Provide user-friendly messages for format violations in the GUI [app.py:_show_neox_error](file:///c:/Users/diesel/Desktop/_parser/app.py#L25).

### Testing (Mandatory)
- All new parsers must include tests in `tests/` using `pytest`.
