# -*- coding: utf-8 -*-
import os, re, sys
from core.dto import MtgDTO

MAGIC = b'\xc1\x59\x41\x0D'

def parse_mtg(file_path):
    """
    Parse de arquivo .mtg NeoX (BXML). 
    Extrai strings legíveis categorizadas por tipo (Shader, Texture, Prop).
    """
    with open(file_path, "rb") as f:
        data = f.read()

    if len(data) < 4 or data[0:4] != MAGIC:
        raise ValueError("Nao e um arquivo NeoX BXML valido (magic incorreto)")

    # Extrator de String Pool (Strings null-terminated com charset printável)
    pattern = re.compile(rb'([a-zA-Z0-9_/.\-]{3,})\x00')
    found_strings = [m.group(1).decode('ascii', errors='ignore') for m in pattern.finditer(data)]
    
    dto = MtgDTO(os.path.abspath(file_path))
    
    seen_sh = set()
    seen_tx = set()
    seen_pr = set()
    
    for text in found_strings:
        text_lower = text.lower()
        
        # 1. Shaders / Tecnicas
        if '.fx' in text_lower or 'shader' in text_lower or 'technique' in text_lower:
            if text not in seen_sh:
                dto.shaders.append(text)
                seen_sh.add(text)
        
        # 2. Texturas
        elif any(ext in text_lower for ext in ['.tga', '.dds', '.png', 'texture', 'map']):
            if text not in seen_tx:
                dto.textures.append(text)
                seen_tx.add(text)
                
        # 3. Atributos XML / Parametros Hash
        else:
            if not text.isdigit() and len(text) > 3 and "Engine" not in text:
                if text not in seen_pr:
                    dto.properties.append(text)
                    seen_pr.add(text)

    # Sort for consistent display
    dto.shaders.sort()
    dto.textures.sort()
    dto.properties.sort()
    
    return dto

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USO: python extract_mtg.py <caminho.mtg>")
    else:
        d = parse_mtg(sys.argv[1])
        print(f"Material: {os.path.basename(d.source_path)}")
        print(f"Shaders:  {d.shaders}")
        print(f"Textures: {d.textures}")
        print(f"Props:    {len(d.properties)} found")
