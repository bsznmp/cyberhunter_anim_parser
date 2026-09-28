# CyberConv.exe — Binary Analysis Report

**Binary:** CyberConv.exe  
**Project:** cuzimfechado  
**Tool:** Cyber Hunter Mesh Convertor — © 2019 Bigchillghost  
**Architecture:** x86 (32-bit) PE, compiled with Visual Studio 2015

---

## 1. Entry Point & Main Function

| Address     | Name                         | Notes                                    |
|-------------|------------------------------|------------------------------------------|
| `0x00408de4` | `entry`                     | PE entry point — calls `__scrt_common_main_seh` |
| `0x00408c75` | `__scrt_common_main_seh`    | MSVC CRT startup; calls `main` via `FUN_004075c0` |
| `0x004075c0` | **`main`** (renamed)        | Actual application main — argc/argv     |
| `0x00407680` | **`process_mesh_file`** (renamed) | Core file parsing & FBX export   |

---

## 2. Main Function Logic (`main` @ 0x004075c0)

```c
int main(int argc, char** argv) {
    // If no arguments: print usage + pause
    if (argc < 2) { print_usage(); system("pause"); return 0; }

    // Loop over all CLI arguments (files)
    for (int i = 1; i < argc; i++) {
        char* ext = strrchr(argv[i], '.');   // find last '.'
        // Compare extension against "mesh" (DAT_0040b728)
        if (strcmp(ext + 1, "mesh") == 0) {
            process_mesh_file(argv[i]);       // process matched file
        }
    }
    return 0;
}
```

**Key observations:**
- `argv` is accessed as a flat `int*` array with stride 4 (32-bit pointer arithmetic): `*(char **)(param_2 + i * 4)`
- File extension comparison uses an **inline manual `strcmp`** loop (byte-by-byte) rather than a library call
- The extension string `"mesh"` is stored at `0x0040B728`
- Only files whose extension matches **`mesh`** (case-sensitive) are processed

---

## 3. Data Structures Identified

### 3.1 Custom Binary `.mesh` File Format

The file format is validated by a magic number at offset 0:

| Offset | Size    | Field                  | Description                                        |
|--------|---------|------------------------|----------------------------------------------------|
| 0x00   | 4 bytes | Magic                  | `0xBBC88034` — file format signature               |
| 0x04   | 4 bytes | Unknown                | Skipped                                            |
| 0x08   | 4 int   | `mesh_type`            | Type flag; `1` = skeletal mesh (has bone data)     |
| 0x0C   | 2 short | `bone_count`           | Number of bones/joints in the skeleton             |
| 0x0E   | variable| Bone records array     | Array of bone descriptor records (see below)       |
| after bones | variable | Mesh geometry     | Vertex, normal, UV, index data (see below)         |

#### Bone Record (per bone, skeletal meshes only)

Each bone record is **0x20 bytes (32 bytes)** for the name, followed by transform data:

| Field              | Size      | Description                                          |
|--------------------|-----------|------------------------------------------------------|
| Name string        | 32 bytes  | Bone name (null-padded)                              |
| Type byte          | 1 byte    | `0x01` = has additional offset data                  |
| Transform offsets  | variable  | XOR-obfuscated float data (XOR mask: `0x80000000`)   |
| Parent index       | 1 byte    | Index of parent bone; `0xFF` = root (no parent)      |
| Bind pose matrix   | 0x40 bytes| 4×4 transform matrix as floats                       |

> **Obfuscation:** Bone transform floats are stored XOR'd with `0x80000000` (flips the IEEE 754 sign bit). The loader reverses this at parse time.

---

### 3.2 Mesh Geometry Buffers (dynamically allocated)

All geometry buffers are heap-allocated with `malloc()` at parse time:

| Variable      | Allocation Size          | Content                                             |
|---------------|--------------------------|-----------------------------------------------------|
| `local_5f0`   | `vertex_count × 0x18`    | **Vertex positions** — 3 × `double` (x, y, z); X is negated on load |
| `local_5a8`   | `vertex_count × 0x18`    | **Vertex normals** — 3 × `double` (x, y, z); X is negated on load  |
| `local_5dc`   | `vertex_count × 0x10`    | **UV coordinates** — 2 × `double` (u, v); V is flipped: `v = 1.0 - v` |
| `local_474`   | `vertex_count × 4 × 0xC` | **Skin weight / index table** — bone index + weight per vertex |
| `local_5ec`   | `face_count × 8`         | **Polygon face index buffer**                       |
| `pvVar14`     | `file_size`              | **Full file image** — entire `.mesh` file read into memory |

**Coordinate system conversion** (mesh → FBX):
- X-axis is **negated** (right-hand → left-hand coordinate flip)
- UV V-channel is **flipped** (`v = 1.0 - v`) for DirectX→OpenGL convention

---

### 3.3 Linked-List Node (FBX Object Node)

Three separate singly-linked lists are built during FBX serialization. Each node is `0x30` bytes (48 bytes), allocated with `malloc(0x30)`:

```c
struct FBX_ObjectNode {
    uint32_t data_lo;    // [+0x00] lower 32 bits of 64-bit node ID or data pointer
    uint32_t data_hi;    // [+0x04] upper 32 bits
    uint32_t value_a;    // [+0x08] e.g., timestamp-derived ID component
    uint32_t value_b;    // [+0x0C] e.g., timestamp-derived ID component (high)
    struct FBX_ObjectNode* next; // [+0x10] pointer to next node (NULL = end)
};
```

Three such lists are maintained:
- **`local_59c` / `local_598`** — Geometry mesh object nodes
- **`local_5a4` / `local_5a0`** — Material/texture object nodes  
- **`puStack_588` / `local_584`** — Model/group object nodes

---

### 3.4 `_SYSTEMTIME` (Windows API Struct)

Used to generate **unique 64-bit object IDs** for FBX nodes based on wall-clock time:

```c
_SYSTEMTIME local_470;
GetLocalTime(&local_470);
// ID = ((hour * 100 + minute) * 100 + second) * 10000 + millisecond
```

Fields used: `wHour`, `wMinute`, `wSecond`, `wMilliseconds`, `wYear`, `wMonth`, `wDayOfWeek`, `wDay`

---

### 3.5 `FILE*` Handles (`_iobuf`)

Two FILE handles are active simultaneously:

| Handle        | Mode   | Usage                                       |
|---------------|--------|---------------------------------------------|
| `local_528`   | `"rb"` | Input `.mesh` file (binary read)            |
| `local_5bc`   | write  | Output `.FBX` file (binary write)           |

---

### 3.6 String Buffers (stack-allocated)

| Variable        | Size      | Usage                                       |
|-----------------|-----------|---------------------------------------------|
| `local_218[256]`| 256 bytes | Extracted filename (without path)           |
| `local_118[260]`| 260 bytes | Output FBX file path (replaces `.mesh` → `.FBX`) |
| `local_488[20]` | 20 bytes  | Holds string `"ByPolygon"` (UV mapping mode)|
| `acStack_454[20]`| 20 bytes | Group name buffer: `"group_0"`, `"group_1"`, … |
| `local_400[12]` | 12 bytes  | Node type string: `"LimbNode"` (bone type)  |

---

### 3.7 Key String Constants (`.rdata`)

| Address      | String          | Purpose                                      |
|--------------|-----------------|----------------------------------------------|
| `0x0040B728` | `"mesh"`        | Expected file extension filter               |
| `0x0040AA78` | `"Mesh"`        | FBX geometry node type name                  |
| `0x0040AA81` | `"Vertices"`    | FBX vertex layer name                        |
| `0x0040AA93` | `"PolygonVert…"`| FBX polygon index layer name                 |

---

## 4. Pseudocode

### 4.1 `main()` — Entry Point Logic

```
FUNCTION main(argc, argv[]):

    IF argc < 2 THEN
        PRINT "Cyber Hunter Mesh Convertor(CyberConv) -- (c)2019 Bigchillghost"
        PRINT usage instructions
        CALL system("pause")
        RETURN 0
    END IF

    FOR i = 1 TO argc - 1 DO
        filename = argv[i]

        // Find the last '.' in the filename to isolate the extension
        ext_ptr = find_last_char(filename, '.')
        extension = ext_ptr + 1   // pointer past the dot

        // Inline byte-by-byte string compare against "mesh"
        IF extension == "mesh" THEN
            CALL process_mesh_file(filename)
        END IF
    END FOR

    RETURN 0

END FUNCTION
```

---

### 4.2 `process_mesh_file(filepath)` — Mesh Parsing & FBX Export

```
FUNCTION process_mesh_file(filepath):

    // ── Step 1: Extract bare filename from full path ──────────────────────────
    filename_only = extract_filename_from_path(filepath)
    output_path   = filepath with ".mesh" replaced by ".FBX"

    // ── Step 2: Open and validate the .mesh file ──────────────────────────────
    file = fopen(filepath, "rb")
    IF file == NULL THEN
        PRINT "error! cannot open file"
        RETURN 1
    END IF

    magic = fread_uint32(file)
    IF magic != 0xBBC88034 THEN
        fclose(file)
        PRINT "Wrong file format!"
        RETURN 2
    END IF

    PRINT "Processing <filename>..."

    // ── Step 3: Read entire file into memory buffer ───────────────────────────
    file_size   = get_file_size(file)
    file_buffer = malloc(file_size)
    fread(file_buffer, file_size, file)
    fclose(file)

    // ── Step 4: Parse file header ─────────────────────────────────────────────
    mesh_type  = read_int32(file_buffer + 0x08)   // 1 = skeletal, 0 = static
    bone_count = read_int16(file_buffer + 0x0C)   // number of bones

    // ── Step 5: Generate unique FBX object IDs from current timestamp ─────────
    time = GetLocalTime()    // _SYSTEMTIME struct
    unique_id = ((time.hour * 100 + time.minute) * 100 + time.second) * 10000
                + time.milliseconds

    // ── Step 6: Open FBX output file ─────────────────────────────────────────
    fbx_file = open_fbx_output(output_path, unique_id, mesh_type)

    // ── Step 7: Parse skeleton (only for skeletal meshes, mesh_type == 1) ─────
    IF mesh_type == 1 THEN

        bone_names_ptr    = file_buffer + 0x0E
        bone_transform_ptr = bone_names_ptr + bone_count * 0x20

        // Check for extra offset data flag
        IF bone_transform_ptr[0] == 0x01 THEN
            bone_transform_ptr += bone_count * 0x1C
        END IF

        bone_weights_ptr = bone_transform_ptr + 1

        // De-obfuscate bone transform floats (XOR sign-bit flip)
        FOR each bone (0 to bone_count - 1):
            FOR each obfuscated float field IN bone_transform:
                float_value = float_value XOR 0x80000000   // flip IEEE 754 sign bit
            END FOR
        END FOR

        // Build skeleton hierarchy (LimbNode entries) in FBX
        bone_node_list = empty linked list
        FOR i = 0 TO bone_count - 1:
            bone_name      = bone_names_ptr[i * 0x20]          // 32-byte name
            parent_index   = bone_weights_ptr[i]               // 0xFF = root
            bind_pose_matrix = read_4x4_matrix(...)            // 0x40 bytes

            // Compute FBX timestamp-based node IDs
            node_id     = unique_id + i + 0x11171
            parent_id   = (parent_index == 0xFF) ? NO_PARENT
                                                  : unique_id + parent_index

            // Add LimbNode to FBX
            CALL write_fbx_limb_node(fbx_file, bone_name, node_id, bind_pose_matrix)
            APPEND node to bone_node_list
        END FOR

        CALL finalize_skeleton(fbx_file, bone_node_list)

    END IF  // end skeletal branch

    // ── Step 8: Parse mesh geometry section ──────────────────────────────────
    // (geometry data follows after bone data in the buffer)

    vertex_count = read from mesh data section
    face_count   = read from mesh data section
    sub_mesh_count = count sub-meshes until type == 1 marker

    // Find UV set
    uv_count = read from mesh section (ushort)
    uv_ptr   = pointer to UV float array

    // Allocate geometry buffers
    positions = malloc(vertex_count * 24)     // 3 doubles per vertex
    normals   = malloc(vertex_count * 24)     // 3 doubles per vertex
    uvs       = malloc(vertex_count * 16)     // 2 doubles per vertex (u, 1-v)
    face_normals_raw = malloc(face_count * 12) // raw uint indices from file
    face_normal_ids  = malloc(face_count * 4)
    polygon_material = malloc(vertex_count * 8) // ByPolygon material indices

    // Read and convert vertex positions
    FOR i = 0 TO vertex_count - 1:
        x = read_float()
        y = read_float()
        z = read_float()
        positions[i] = (-x, y, z)    // negate X for coordinate system flip
    END FOR

    // Read and convert vertex normals
    FOR i = 0 TO vertex_count - 1:
        nx = read_float()
        ny = read_float()
        nz = read_float()
        normals[i] = (-nx, ny, nz)   // negate X for coordinate system flip
    END FOR

    // Skip optional tangent / bitangent layers if present (flagged by bytes)

    // Read face normal indices (bit-flipped in file: ~index)
    FOR i = 0 TO face_count - 1:
        raw = read_uint16()
        face_normals_raw[i] = ~raw   // bitwise NOT to recover actual index
    END FOR

    // Read and convert UV coordinates
    FOR i = 0 TO vertex_count - 1:
        u = read_float()
        v = read_float()
        uvs[i] = (u, 1.0 - v)        // flip V for DirectX → OpenGL convention
    END FOR

    // Build per-polygon material index array ("ByPolygon" mapping)
    poly_id = 0
    FOR each sub_mesh s (0 to sub_mesh_count - 1):
        face_count_s = sub_mesh_face_counts[s]
        FOR j = 0 TO face_count_s - 1:
            polygon_material[poly_id] = s
            poly_id++
        END FOR
    END FOR

    // ── Step 9: Build skin weights (skeletal meshes only) ─────────────────────
    IF mesh_type == 1 THEN
        skin_table = malloc(vertex_count * 4 * 12)
        FOR i = 0 TO vertex_count - 1:
            FOR w = 0 TO 3:     // up to 4 bone influences per vertex
                bone_idx = read_byte()           // 0xFF = no influence
                weight   = read_float()
                skin_table[i].influences[w] = (bone_idx == 0xFF) ?
                                              (0x7FFFFFFF, weight, i) :
                                              (bone_idx,   weight, i)
            END FOR
        END FOR
    END IF

    // ── Step 10: Serialize geometry to FBX ───────────────────────────────────
    geom_node_id   = unique_id + 0x7531
    model_node_id  = unique_id + 0x4E21

    geom_list  = build_linked_list_node(geom_node_id,  positions, normals, uvs)
    model_list = build_linked_list_node(model_node_id, sub_mesh_count)

    // Write FBX header/timestamp block
    CALL write_fbx_objects_section(fbx_file, geom_list, model_list)

    // Write each sub-mesh as a separate FBX group model
    FOR i = 0 TO sub_mesh_count - 1:
        group_name = "group_" + str(i)
        CALL write_fbx_model_node(fbx_file, group_name, node_id++)
    END FOR

    // Write connections between geometry ↔ model ↔ skeleton nodes
    CALL write_fbx_connections(fbx_file, geom_list, model_list, bone_node_list)

    // Write FBX takes / animation stubs
    CALL write_fbx_takes(fbx_file, ...)

    // Record output file size / patch offsets
    end_offset = ftell(fbx_file)
    fseek(fbx_file, stored_offset_location, SEEK_SET)
    fwrite(end_offset)

    // ── Step 11: Cleanup ──────────────────────────────────────────────────────
    free_linked_list(geom_list)
    free(positions)
    free(normals)
    free(uvs)
    free(polygon_material)
    free(file_buffer)

    PRINT "finished"
    RETURN 0

END FUNCTION
```

---

### 4.3 `FBX_ObjectNode` — Linked List Operations (pseudocode)

```
STRUCT FBX_ObjectNode:
    data_lo  : uint32   // low  32 bits of 64-bit node ID
    data_hi  : uint32   // high 32 bits of 64-bit node ID
    value_a  : uint32   // timestamp-derived component A
    value_b  : uint32   // timestamp-derived component B
    next     : ptr      // → next node, or NULL if tail


FUNCTION build_linked_list_node(id_lo, id_hi, val_a, val_b) → node_ptr:
    node = malloc(0x30)        // 48 bytes
    IF node == NULL THEN
        PRINT "memory allocation failed!"
        RETURN existing_head   // graceful fallback
    END IF

    node.data_lo = id_lo
    node.data_hi = id_hi
    node.value_a = val_a
    node.value_b = val_b
    node.next    = NULL

    // Append to tail of existing list
    IF list_tail != NULL THEN
        list_tail.next = node
    END IF
    list_tail = node

    RETURN (list_head == NULL) ? node : list_head

END FUNCTION
```

---

## 5. Summary

**CyberConv.exe** is a command-line **3D mesh file converter** that:
1. Reads a proprietary binary **`.mesh`** format (magic: `0xBBC88034`) used in *Cyber Hunter* (mobile game)
2. Supports both **static meshes** and **skeletal (skinned) meshes** (flagged by byte at offset 0x08)
3. Converts geometry (vertices, normals, UVs, skin weights) and skeleton (bones + bind-pose matrices) into **Autodesk FBX** binary format
4. Uses **timestamp-derived 64-bit IDs** for FBX object nodes
5. Applies coordinate-system fixups: **X-axis negation** and **UV V-flip**

### Data Structure Summary Table

| Structure             | Type               | Key Detail                              |
|-----------------------|--------------------|-----------------------------------------|
| `.mesh` file header   | Custom binary      | Magic `0xBBC88034`, bone count at 0x0C  |
| Bone record           | Fixed-size struct  | 32-byte name + XOR-obfuscated transforms|
| Vertex/normal buffers | `double[]` arrays  | Heap-allocated, 24 bytes per vertex     |
| UV buffer             | `double[]` array   | Heap-allocated, 16 bytes per vertex     |
| FBX object node       | Singly linked list | 48-byte nodes, `malloc(0x30)`           |
| `_SYSTEMTIME`         | Windows API struct | Used for unique FBX node ID generation  |
| `FILE*` handles       | CRT `_iobuf`       | Input `.mesh` (rb) + Output `.FBX` (wb) |
| String buffers        | Stack `char[]`     | Filename, group names, type names       |
