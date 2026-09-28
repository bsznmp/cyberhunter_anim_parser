3D Model Guide
From XentaxWiki

This is a work-in-progress and open to any edits. You may add any information that you feel would be useful, and modify any existing information that may be inaccurate or could be improved. No permission is required. Of course, as this is an open page, "If you don't want your writing to be edited mercilessly, then don't submit it here."

Contents
1 Preface
2 Introduction
3 Common data
3.1 Vertices
3.2 Faces
3.3 Bones
3.4 Animation
3.5 Morphs
3.6 Materials
4 Exploring a Model Format
4.1 Where do I begin?
4.2 Common Patterns
4.2.1 Chunk-based format
4.2.2 Offset tables
4.2.3 Material index ranges
4.3 Techniques
4.3.1 Using a calculator
4.3.2 Comparing multiple files
5 A simple model format
6 Tools
6.1 Hex Viewers
6.2 3D Model Viewers/ 3D Modellers
7 Links


Preface
This page will briefly describe how to reverse a 3D model format. This will not be a tutorial on how to read hex, but instead on various concepts used in 3D computing and rendering that will help make sense of what the data represents.

For a more detailed list of 3D concepts, check out the 3D model glossary

Introduction
Please read the Definitive Guide to Exploring File Formats before starting this guide, which is aimed specifically for 3d file formats. It is assumed that you know how to read files in hex viewers.

No knowledge in 3d is needed, however, any experience in 3d modelling or 3d programming will help. No advance math knowledge is used in 3d formats, though it is in 3d programming, but those are usually hidden inside 3d libraries you use, like your 3d engine or your 3d modeller's scripting language. You should be able to understand what vectors and matrices are though.

Common data
The following a list of things that you should look out for when you're exploring a 3D format. Note that in addition to data related to 3D models, the developers may choose to store other data with it that are only useful for to their engine or scripts. This miscellaneous data typically is not important and can be skipped by your parser.

Each item will also indicate how they are "typically" represented. Note that very often, 8-byte, 4-byte, or 2-byte floats may be used for precision or to optimize space. But 4-byte floats are more often used, so when you're working with float data, if one type doesn't work try another.

Vertices
Data that is usually stored with vertices.

Vertex coordinates. Three floats
Vertex normals. Three floats
Texture coordinates UV(W). Two floats. Three if the W-value is specified.
Vertex colors. Four floats
Vertex weights
Bone indices

Faces
Data that may be stored with faces.

- Vertex indices
- Normal indices
- UV indices
- Material indices
- Face Normals (in addition to each vertex having a normal, each face can also have a normal)

Bones
- Bone index
- Parent bone index
- Bone name
- Bone transformation.

Animation

Morphs

Materials

Exploring a Model Format

Where do I begin?
Naturally, if you have no experience with format reversing, you will probably have no clue where to start. Even if you do, you probably still won't know where to start. Some things that you might want to consider before tackling your own format:
- Get some decent tools. Some are better than others.
- Familiarize yourself with the API you're working with
- Look at existing formats and write a parser for it
- Get a feel for various patterns that arise in various formats. After awhile these things become second-nature.

Common Patterns
Design patterns often arise in file formats, due to various reasons. This is also true in model formats.

Chunk-based format
This format essentially structures all of the data into data "chunks" or "blocks", where each chunk is identified by an ID and often has a size associated with it.

"In this kind of file structure, each piece of data is embedded in a container that contains a signature identifying the data, as well the length of the data (for binary encoded files). This type of container is called a "chunk". The signature is usually called a chunk id, chunk identifier, or tag identifier." -- Wikipedia

It is usually easy to identify this format because strings are usually used as the chunk ID, but numbers can be used as well.

If you suspect that the format uses a chunk-based format, consider examining a few of the values that you believe are the chunk sizes and see if you can parse the entire file without having to understand any of the data.

Offset tables
Material index ranges
Face material information may be stored in the form of index or face ranges. For example, if a particular mesh is composed of 3000 face indices and used 3 materials, the first material might be assigned to indices 0 to 799, the second material from 800 to 2045, and the third material from 2046 to 2999 (assuming zero-based indexing). If you find yourself with some unknown integers that add up to the total number of indices or faces, you might want to try this out.

Techniques
Some techniques that you might use to help figure out what kind of data you might be looking at.

Using a calculator

Comparing multiple files

A simple model format
Here is a simple model format: http://forum.xentax.com/viewtopic.php?f=29&t=3739 (temporarily just linking to an existing tutorial)

Tools
You will need two things
- A hex viewer
- A 3D model viewer/ 3D modeller
This is the bare minimum required to get started on your model reversing journey, but your choice of tools may make your experience easier or more challenging. Of course if you are working with a text format you won't need a hex viewer, but more often than not you will be working with binary formats.

Some common tools are listed below. It is by no means an exhaustive list. Try different tools to get a feel for what you like. Links are available at the end of the page.

Hex Viewers
- 010 Editor
- - 30-day trial, US$50 license
- - Comes with many useful features.
- HxD
- - Free
- - Simple hex editor.
- Hex Workshop
- - 30-day trial, US$90 license

3D Model Viewers/ 3D Modellers
There are many packages for model editing. There are dozens of custom model viewers. The more common ones are as follows:

- 3D Studio Max
- - 30-day trial, US$3500 license
- - Comes with its own scripting language for importing models.
- Blender
- - Free
- - Uses Python scripts to import models.
- Noesis
- - Free
- - Provides C++ and python API's for importing models.
- Metasequoia
- - Free*, US$45 license
- - Simple 3D editor. Does not support too many things, but it gets the geometry out. The MQO format is very simple as well.
Note that the free version comes with limited features.

Links
- Blender - http://blender.org
- Python - http://python.org/
- Noesis - http://oasis.xentax.com/index.php?content=home
- Metasequoia - http://metaseq.net/english/



>>> 
Very Basic model format conversion (Shaiya)

In this tutorial you will learn the VERY basic way to convert a 3d model into verts that can be loaded into a 3d application.
I hope to expand on these tutorials and use better tools to automate the job and code it completely proper.
for this tutorial you will need a few tools

1. Float 2 text download/file.php?id=1888
2. HxD (free hex editor)
3 excel (2007)
4 Deep exploration (program able to view an obj with just verts
5 some shaiya model files. download/file.php?id=2187

1) Ok so open the model folder after you extract them and open the file demf_boots001.3DC
in the program HxD
Image

2)Now if we know the model format lets see how to break it down
```
#Provided from Fatduck
dword constant00
dword numBones
struct Bone {
float_16 Matrix4X4
}
dword numVerts
struct Vert {
float_3 CoordXYZ
float Weight
byte BoneID01
byte BoneID02
byte NULL1
byte NULL2
float_3 NormalXYZ
float_2 TexCoordUV
}
dword numFaces
struct Face {
word_3 FaceIndices123
}
```

3) a dword is 4 bytes
a 32 bit float (these are 32 bit floats) is equal to 4 bytes
float_X is the number of floats in a row so float_2 would be 8 bytes
and a byte is 1 byte
a word is 2 bytes

4) So knowing this lets look at the first line
dword constant00
this tells us our first 4 bytes are 00 and if we check this they are
Image

5) The next line is
dword numBones
so the Number of bones is in the next 4 bytes
which shows us 2C 00 00 00 so that converts into 00 00 00 2C
and 2C in decimal is 44
so now we know we have 44 bones
Image

6) The next part is
struct Bone {
float_16 Matrix4X4
}
so this means we have a float which is 4 bytes then the underscore 16 means each bone has 16 floats
so in decimal we do 4 x 16 = 64 then we convert this number to hex which is 0x40
we multiply 0x40 bye the number of bones 2C and we get B00
If you highlight this section you should get a screen looking just like mine

7) The next line is
dword numVerts
this means the next 4 bytes tell us how many verts we will have in our model
so we take AE 01 00 00 and convert it to 00 00 01 AE and that equals 430
so there are 430 vertexes.
Image

8) The next line is the most important for the tutorial
float_3 CoordXYZ
this means we have a float which is 4 bytes and we have 3 in a row representing x , y z coordinates.
so our first set of cordiantes should look like this
X)FE F8 A1 BE
Y)00 00 C8 36
Z)4A CA BF BD
Image

9) The next line
float Weight
means the next 4 bytes are the weighting information
00 00 80 3F

10) the next 4 lines tell us what bones our weighting information has influence on
byte BoneID01
byte BoneID02
byte NULL1
byte NULL2
22 00 00 00
break these apart byte by byte so this vertex is effected bye bone 22 and 00
you can ignore the NULL parts

11) This next line tells us our normal coordinates
float_3 NormalXYZ
it is a float value so its 4 bytes and it is in a series of 3 so its 12 bytes total
X)08 7D 7D BF
Y)E2 5A 0D 3E
Z)AC 99 B1 BC

12) The last line of the vertex definition tells us our UV coordinates.
float_2 TexCoordUV
U)BB DA 08 3F
V)F2 60 7A 3F
so it is again a float of 4 bytes and there are 2 in a row so it is 8 bytes total

13) The next line tells us how many faces we have
dword numFaces
so it is a dword of 4 bytes
98 01 00 00 so convert it to 00 00 01 98 and in decimal that is 408
so we have 408 Faces

14) The next 2 lines tell us the face structure
struct Face {
word_3 FaceIndices123
}
so we have a word 2 bytes and 3 in a row so thats 6 bytes
so 408 / 3 = 158

15) Now to the converting the vertex part
highlight the whole vertex section and copy it into a new hxd file called vertex.dat
start offset B0C
end offset 4E3B
length 4330

16) now we use float2txt on our dat file
float2txt.exe vertex.dat vertex.txt 10
we take the arguments float2txt.exe input file output file number of floats
we choose 10 because there are 10 groups of 4 bytes that make up our vertex structure.

17) now we open excel and it will ask is this a delimited file choose tab and space check boxes and hit import.
you will end up with columns a - j
Image
18) delete columns d - j so you are only left with
a b and c
inert a column before a and fill it with the letter v until you reach the end of your vertex list
(line 430)

19) save the file as a csv file
open the file in hxd
do a replace and replace in hex 2C with 20
and save the file as testobj.txt

20) now open your file in wordpad and paste the following header

Code: Select all
# 3ds Max Wavefront OBJ Exporter v0.94b - (c)2007 guruware
# File Created: 26.09.2009 19:47:31

mtllib test.mtl

#
# object NET
#

and at the end of your file put

Code: Select all
# 430 vertices
ok now save your file as test.obj

21) Open your file in deep exploration and see the boots :)
Image