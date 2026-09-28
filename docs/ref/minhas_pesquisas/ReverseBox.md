https://github.com/bartlomiejduda/ReverseBox
From: bartlomiejduda

Info
ReverseBox is a Python package with a set of functions useful in software reverse engineering.

Why ReverseBox?
It's designed to help with:

Decompressing / compressing data
Decrypting / encrypting data
Tedious reverse engineering tasks e.g. testing different checksum algorithms to find the one that was used in the software or file format
Figuring out file formats
Parsing data structures
Wrapping functions for input/output operations
Searching for raw images
Who should use ReverseBox?
Mostly developers and reverse engineers (e.g. file format researchers or software researchers).

List of functionalities
Checksum

Adler32 ✔️
Cocos2d PVR ✔️
Fletcher16 ✔️
Fletcher32 ✔️
Internet Checksum / IPv4 header checksum ✔️
Sum8 ✔️
Sum8 2s Complement ✔️
Unix Sum BSD16 ✔️
Unix Sum SYSV ✔️
Xor8 ✔️
CRC

CRC-8 ✔️
CRC-8/CDMA2000 ✔️
CRC-8/DARC ✔️ (wrapper only)
CRC-16 (ARC) ✔️
CRC-16 (Modbus) ✔️
CRC-16 (Sick) ✔️
CRC-16 (DNP) ✔️
CRC-16 (EA CRCF) ✔️
CRC-16-CCITT (XModem) ✔️
CRC-16-CCITT (0xFFFF) ✔️
CRC-16-CCITT (0x1D0F) ✔️
CRC-16-CCITT (Kermit) ✔️
CRC-32/CKSUM (Unix cksum) ✔️
CRC-32 (ISO/HDLC) ✔️
CRC-32 (Asobo) ✔️
CRC-64 (Asobo) ✔️
CRC-64/GO-ISO ✔️ (wrapper only)
Compression

Asobo (TODO) ❌
BZE/BZZ (TODO) ❌
BZIP2 ✔️ (wrapper only)
GZIP (TODO) ❌
JCALG1 (TODO) ❌
LZ4 ✔️ (wrapper only)
LZMA ✔️ (wrapper only)
LZO / LZO1X ✔️ (wrapper only)
LZSS (TODO) ❌
MIO0 ✔️
NitroSDK (TODO) ❌
Oodle (TODO) ❌
Refpack (EA Games) ✔️ (wrapper only)
RNC (TODO) ❌
ZLIB ✔️ (wrapper only)
PS2 GS Texture Compression ✔️
RLE TGA ✔️
RLE TGA (reversed condition) ✔️
PackBits (Macintosh RLE) ✔️
(game-specific) Re:Tiyoruga DAT compression ✔️
(game-specific) Intelligent Games Custom Huffman ✔️
(game-specific) Executioners RLE ✔️
(game-specific) Emergency RLE ✔️
(game-specific) Neversoft RLE ✔️
(game-specific) Tzar RLE ✔️
(game-specific) Leapster RLE ✔️
Encryption

AES (TODO) ❌
DES (TODO) ❌
Lucifer / DTD-1 (TODO) ❌
ROT13 ✔️
XOR Cipher (Basic) ✔️
XOR Cipher (Basic) Guesser ✔️
Hatch Engine Encryption ✔️
(game-specific) XOR Cipher (Retro64 ECO) ✔️
(game-specific) XOR Cipher (Giana’s Return ZDA) ✔️
Hash

Additive Hash ✔️
AP ✔️
DJB2 ✔️
RX3 ✔️
FNV0-32 ✔️
FNV0-64 ✔️
FNV1-32 ✔️
FNV1-64 ✔️
FNV1A-32 ✔️
FNV1A-64 ✔️
Jenkins one-at-a-time ✔️
SDBM ✔️
SHA-1 ✔️ (wrapper only)
SHA-2 (256 bits) ✔️ (wrapper only)
MD2 ✔️ (wrapper only)
MD5 ✔️ (wrapper only)
Murmur3 ✔️ (wrapper only)
(game-specific) Hercules (TODO) ❌
(game-specific) E-racer (TODO) ❌
(game-specific) Pivotal Games DAT Hash ✔️
Image

3DS Swizzling/Twiddling ✔️
CMPR Swizzling/Twiddling ✔️
PS2 Swizzling/Twiddling ✔️
PS2 Palette Swizzling/Twiddling ✔️
PS4 Swizzling/Twiddling ✔️
PS5 Swizzling/Twiddling ✔️
PSP Swizzling/Twiddling ✔️
PS Vita Swizzling/Twiddling ✔️
XBOX 360 Swizzling/Twiddling ✔️
GameCube/WII Swizzling/Twiddling ✔️
Switch Swizzling/Twiddling ✔️
WII U Swizzling/Twiddling ✔️
XBOX/PS3 Swizzling/Twiddling (Morton Order) ✔️
Dreamcast Swizzling/Twiddling (Morton Order) ✔️
BC Swizzling/Twiddling ✔️
PS2 GS Texture Swizzling/Twiddling ✔️
Generating mipmaps ✔️
Decoding and encoding images with pixel formats
mentioned in the following table:
Pixel Format	Decode support	Encode support
RGB121	✔️	❌
ALPHA4	✔️	❌
ALPHA4_17X	✔️	✔️
RGB121_BYTE	✔️	❌
RGBA2222	✔️	❌
RGBX2222	✔️	❌
GRAY8	✔️	❌
ALPHA8	✔️	❌
ALPHA8_17X	✔️	❌
LA44	✔️	❌
RGBX332 (RGB8)	✔️	❌
BGRX332 (BGR8)	✔️	❌
RGB565	✔️	✔️
BGR565	✔️	✔️
RGBX5551	✔️	✔️
RGBT5551	✔️	✔️
BGRT5551	✔️	❌
RGBA5551	✔️	✔️
BGRA5551	✔️	✔️
BGRA5551_TZAR	✔️	❌
BGRX5551	✔️	❌
RGBX6666	✔️	❌
RGBA6666	✔️	❌
RGB888 (RGB24)	✔️	✔️
BGR888 (BGR24)	✔️	✔️
ARGB4444	✔️	❌
RGBA4444	✔️	❌
ABGR4444	✔️	✔️
XBGR4444	✔️	❌
RGBX4444	✔️	✔️
BGRA4444	✔️	✔️
BGRA4444_LEAPSTER	✔️	❌
BGRX4444	✔️	❌
XRGB1555	✔️	❌
ARGB1555	✔️	❌
ABGR1555	✔️	❌
XBGR1555	✔️	❌
ARGB8888	✔️	✔️
ABGR8888	✔️	❌
RGBA8888	✔️	✔️
BGRA8888	✔️	✔️
XRGB8888	✔️	❌
RGBX8888	✔️	❌
XBGR8888	✔️	❌
BGRX8888	✔️	❌
BGRT8888	✔️	❌
BGRA8888_TZAR	✔️	❌
RGB48	✔️	❌
BGR48	✔️	❌
PAL4	✔️	✔️
PAL8	✔️	✔️
PAL8_TZAR	✔️	❌
PAL16	✔️	❌
PAL32	✔️	❌
PAL_I8A8	✔️	❌
N64_RGB5A3	✔️	❌
N64_BGR5A3	✔️	✔️
N64_I4 / GRAY4	✔️	✔️
N64_I8 / GRAY8	✔️	✔️
N64_IA4	✔️	✔️
N64_IA8	✔️	✔️
N64_RGBA32	✔️	❌
N64_CMPR	✔️	✔️
BC1/DXT1	✔️	✔️
PSP_DXT1	✔️	❌
DXT2	✔️	❌
BC2/DXT3	✔️	✔️
PSP_DXT3	✔️	❌
DXT4	✔️	✔️
BC3/DXT5	✔️	✔️
PSP_DXT5	✔️	❌
BC4	✔️	✔️
BC5	✔️	✔️
BC6	✔️	✔️
BC7	✔️	✔️
PVRTCI_2bpp_RGB	✔️	✔️
PVRTCI_2bpp_RGBA	✔️	✔️
PVRTCI_4bpp_RGB	✔️	✔️
PVRTCI_4bpp_RGBA	✔️	✔️
PVRTCII_2bpp	✔️	✔️
PVRTCII_4bpp	✔️	✔️
ETC1	✔️	✔️
BW1bpp	✔️	✔️
SharedExponentR9G9B9E5	✔️	✔️
RGBG8888	✔️	✔️
GRGB8888	✔️	✔️
ETC2_RGB	✔️	✔️
ETC2_RGBA	✔️	✔️
ETC2_RGB_A1	✔️	✔️
EAC_R11	✔️	✔️
EAC_RG11	✔️	✔️
ASTC_4x4	✔️	✔️
ASTC_5x4	✔️	✔️
ASTC_5x5	✔️	✔️
ASTC_6x5	✔️	✔️
ASTC_6x6	✔️	✔️
ASTC_8x5	✔️	✔️
ASTC_8x6	✔️	✔️
ASTC_8x8	✔️	✔️
ASTC_10x5	✔️	✔️
ASTC_10x6	✔️	✔️
ASTC_10x8	✔️	✔️
ASTC_10x10	✔️	✔️
ASTC_12x10	✔️	✔️
ASTC_12x12	✔️	✔️
ASTC_3x3x3	✔️	✔️
ASTC_4x3x3	✔️	✔️
ASTC_4x4x3	✔️	✔️
ASTC_4x4x4	✔️	✔️
ASTC_5x4x4	✔️	✔️
ASTC_5x5x4	✔️	✔️
ASTC_5x5x5	✔️	✔️
ASTC_6x5x5	✔️	✔️
ASTC_6x6x5	✔️	✔️
ASTC_6x6x6	✔️	✔️
BASISU_ETC1S	✔️	✔️
BASISU_UASTC	✔️	✔️
RGBM	✔️	✔️
RGBD	✔️	✔️
GST121	✔️	❌
GST221	✔️	❌
GST421	✔️	❌
GST821	✔️	❌
GST122	✔️	❌
GST222	✔️	❌
GST422	✔️	❌
GST822	✔️	❌
YUY2	✔️	❌
NV12	✔️	❌
NV21	✔️	❌
UYVY	✔️	❌
YUV444P	✔️	❌
YUV410P	✔️	❌
YUV420P	✔️	❌
YUV422P	✔️	❌
YUV411P	✔️	❌
UYYVYY411	✔️	❌
YUV440P	✔️	❌
YUVA420P	✔️	❌
AYUV	✔️	❌
GRAY8A (LA88)	✔️	❌
GRAY16	✔️	❌
RG88	✔️	❌
R8	✔️	❌
G8	✔️	❌
B8	✔️	❌
R16	✔️	❌
G16	✔️	❌
B16	✔️	❌
R32	✔️	❌
G32	✔️	❌
B32	✔️	❌
BUMPMAP_SR	✔️	❌
IO
File Reader ✔️
File Writer ✔️
Bytes Handler ✔️
Translation Text Handler ✔️
Mod Handler ✔️
File extension checking ✔️
Padding calculation ✔️
File size checking ✔️
Checksum calculation - example
// CRC32 calculation

from reversebox.crc import crc32_iso_hdlc
from reversebox.common import common

test_data = b'123456789'
crc32_handler = crc32_iso_hdlc.CRC32Handler()
crc32 = crc32_handler.calculate_crc32(test_data)
print("CRC32_INT: ", crc32)
print("CRC32_STR: ", common.convert_int_to_hex_string(crc32))
// CRC32 output

CRC32_INT:  3421780262
CRC32_STR:  0xCBF43926
XOR encryption - example
// XOR Cipher (Basic)

from reversebox.encryption.encryption_xor_basic import xor_cipher_basic


test_data = b'abcd'
test_key = b'\x3D'
xor_result = xor_cipher_basic(test_data, test_key)
print(xor_result)
// XOR Cipher output

b'\\_^Y'
File Handler - example
// File reading

import os
from reversebox.io_files.file_handler import FileHandler


file_path = os.path.join(os.path.dirname(__file__), "file.bin")
file_reader = FileHandler(file_path, "rb")
file_reader.open()
value = file_reader.read_str(4, "utf8")
print(value)
// File Reader Output

ABCD
Hash calculation - example
// SHA-1 calculation

from reversebox.hash.hash_sha1 import SHA1Handler

test_data = b'abcd'
sha1_handler = SHA1Handler()
sha1 = sha1_handler.calculate_sha1_hash(test_data)
print("SHA-1 hash: ", sha1)
// SHA-1 Output

SHA-1 hash:  b'\x81\xfe\x8b\xfe\x87Wl>\xcb"Bo\x8eW\x84s\x82\x91z\xcf'
Image decoding - example
// DXT1 compressed image decoding

from reversebox.image.image_decoder import ImageDecoder
from reversebox.image.image_formats import ImageFormats
from reversebox.image.pillow_wrapper import PillowWrapper


def show_img():
    with open("image_data_dxt1_64x64.bin", "rb") as f:
        image_data = f.read()

    img_width: int = 64
    img_height: int = 64
    decoder = ImageDecoder()
    wrapper = PillowWrapper()
    converted_data: bytes = decoder.decode_compressed_image(image_data, img_width, img_height, ImageFormats.BC1_DXT1)
    pil_image = wrapper.get_pillow_image_from_rgba8888_data(converted_data, img_width, img_height)
    pil_image.show()


if __name__ == '__main__':
    show_img()
More Examples
Need more examples?
Check out list of tools written using ReverseBox:

Giana's Return ZDA Tool
ObsCure 2 HVP Extractor
Tail Concerto Translation Tools
EA Graphics Manager
Acclaim TRE Tool
F-Zero X TEX Tool
ImageHeat
Hatch Engine Archive Tool
ReverseBox Demo
Super Galdelic Hour .egg texture extractor/converter
and more...