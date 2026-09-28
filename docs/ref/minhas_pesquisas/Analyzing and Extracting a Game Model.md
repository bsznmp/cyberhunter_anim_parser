Part III. Analyzing and Extracting a Game Model

Now we're about to officially start our journal of exploring a game archive.
First you'll need a proper hex editor. My recommendation would be HexEdit. And that's what I'm going to introduce in this tutorial. Get the latest version here.

Now we're about to officially start our journal of exploring a game archive.
First you'll need a proper hex editor. My recommendation would be HexEdit. And that's what I'm going to introduce in this tutorial. Get the latest version. HexEdit5build1349.zip

This is how its UI looks like:

image.thumb.png.64caaf2eebde024e3cfbff2055027682.png

A few fields that you need to pay attention to:
The Offset Field: It records every address of the loaded file by columns and rows. By default the number of columns is set to 16 (0x10 in hex), but you can always expand them if you want to.
Hex View: The true nature of a file, which is consisted of an array of bytes. Each byte is represented by a two-digit hex number.
Text View: It converts each byte into human readable texts according to the ASCII table.
Toolbars: Here you can find some very useful functions. Choose what you need by navigating to View>Toobars. The most frequently used functions are the Calculator, the Bookmarks, and the Properties.

 

Now it comes to the practical part. I'll take Marvel Avengers: Battle for Earth on Xbox 360 as an example. We're not going to start from the original
game archives, but the extracted .nif files that contain the models.
Download the example files here.

The file we're going to work with is skrull_skin_m.nif. Let's open it in HexEdit. There're some strings at the front part of the file.
We're not going to reverse the entire file structure since we only need the models. So let's focus on the geometry data.

Usually it would be easier to locate the geo data by looking for the face buffer. As face indices are stored as an array of integers, they usually look like a regular
character table in the text view instead of some random bytes.

Scroll down and we'll find the indices buffer approximately at offset 0x6760:

image.png.0e4e642437162210d194ee77d9d6b3b2.png

Let's keep that in mind, or we can set a bookmark with HexEdit here and return later. Now continue to scroll down. Then we find the structure
changed around 0xE780.

image.png.1d8a96ac41f2aae1f024b3ceaa0bdc8c.png

These compact data should be the vertices chunk. Note that it doesn't have to come after the face buffer. Sometimes it could be at the front.
But in this case, since the data before the face indices doesn't look compact, basically we can draw the conclusion.

Vertex data are defined as array(s) of vertex elements, and depending on the type of element making up the array(s), there're two most common structure of vertex data: "separate" and "structured".

"separate"
Separate arrays for every type of vertex attributes are defined, and they're placed in file one after another:

vertex positions
[
	v1 x y z;
	v2 x y z;
	v3 x y z;
	...	
]
vertex normals
[
	vn1 x y z;
	vn2 x y z;
	vn3 x y z;
	...	
]
vertex UVs
[
	vt1 u v;
	vt2 u v;
	vt3 u v;
	...	
]
"structured"
A structure of all vertex attributes is defined, of which the vertex array is made:

Vertex Array
[
	{v1 x y z, vn1 x y z, vt1 u v};
	{v2 x y z, vn2 x y z, vt2 u v};
	{v3 x y z, vn3 x y z, vt3 u v};
	...
]
 

Next we need to figure out the size of one element of the array.

The sequence bytes 00 10 catch our eyes at the first glance.

image.png.edbfb72a50579bc4928e782b0490612e.png

And there're always 0x30 (48 in decimal) bytes between the former and the latter one.
So let's expand the number of columns to 48, and we got this in the text view:

image.png.55765d0d84e8d083ad1a4c65d909a601.png

As you can see the bytes are aligned into a vertical pattern. So now every element of the array is hold exactly in one row. But to find the start of it we need to look at the binary values in the hex view.
Now it's time to explain you how endianness works.

Endianness refers to the order in which the bytes of a multi-byte word are stored in memory. So the 4-byte value 0x11223344 is stored as 44 33 22 11 for little-endian, and 11 22 33 44 for big-endian.

Usually Windows, PS4 and Android file systems use little endianness, while console file systems, like Wii, PS3 and Xbox 360, are using big endianness.

As I've mentioned before the game we're working with is for Xbox 360, so the file is in big-endian.

Now we switch to the hex view:

image.png.f8fa0e3eaf53840a584263bf068e4b5d.png

We can easily identify that the sequence before the highlighted field is 00 04 02 34 instead of the expected 00 00 3C 00, which means the start offset of the vertices is 0xE7C3. The end offset should be at the same column when the data is aligned. We scroll down and find its end at 0x358B3:

image.png.ef165a7bb457e263130f2c52a9dcc597.png

You can see that the byte after 0x358B3 is not 0x2C but 0x01, which makes clear our earlier claim. As HexEdit shown, the total size of the vertex chunk is 0x270F0 ( = 0x358B3 - 0xE7C3). We devide it by 0x30, then we have the vertices count: 0xD05(3333).

Now let's do a little more research on the vertex format. Obviously it won't be the "separate" type as the vertex size 48 has already exceeded the maximum amount of bytes needed to store the 3 coordinates x, y and z (even if they use double type it costs merely 24 bytes). So it's "structured" for sure.

And we noticed that the sequence 3C 00 seems to be used for distinguishing different elements. We encounter the first 3C 00 after skipping 10 bytes from 0xE7C3.

10 bytes are barely enough to hold 3 floats(= 12 bytes), so the data type could be short or half-float, both of which use 2 bytes. But there're still 4 bytes left, and naturally we will assume that to be another two shorts or half-floats for UVs.

Then right after the first 3C 00, there're 6 bytes following by another 3C 00, and this pattern repeats for 3 times. Assuming they are all two-byte values, they could be the normal, binormal and tangent vectors. That sounds quite reasonable.

image.thumb.png.62999245df33ba2500d2e08d8cbbf208.png

Now let's open this file in Hex2Obj. Press litE to change the endianness to big-endian, seq to handle "structured" data, noPtC to
switch to display as point cloud, and fill in the start offset and count of the vertices.

image.png.e90f4cf46d65d51a3af7b25ef00f3172.png

For the data type of the vertices, let's try short type first.
After clicking the mesh button we got the point cloud shown as in the left figure.

image.thumb.png.bee4a90acf080a88e45151c9f8fc229e.png

Seems that is the UVs as we can see they' ll overlap if their 3rd coordinates are flatten. So let's change the offset to 0xE7C7 to
skip these two values. The point cloud is as shown in the middle figure.

It doesn't look correct though. Perhaps we should try with half-float now. Then we get the correct result as shown in the right figure.

So we can say that the data type of the vertices is half-float.

After that let's return to the face indices block, which is at 0x6760 if you don't remember.
We know that our vertices count is 3333 < 65535(maximum value that an unsigned short can represent), so the indices should be using short intergers.

All game models' face indices are stored as triangles (including those encoded as trixstrips), which means every face is represented by 3 indices. Usually the indices are stored in an increasing order so for most of the cases the first face will be 0, 1, 2.
Base on these info, plus we've already known the endianness, it's not hard to locate its start: 0x6764.

image.png.0e28d6289eff45042fdb7738ebc23d81.png

The sequence 00 01 02 15 seems more like some signature bytes(indeed it is), and it'll break the regularity if we take it into acount as part of the buffer.
Besides, we can always correct that if our intuition failed.

To get the indices count, we'll need to find where it ends. There's an easy way to do that if the faces are defined as a triangle list.
We scroll down to where the pattern changed, then set the number of columns to 3 x 2(the size of the indices data type), which is 6.
And the last index should end at the same column as the first one.

image.png.bb45f5bdac845987b62f24cc763a25c9.png

So it ends at 0xE786. It's impossible to be 0xE78C as 0xF000 has far exceeded the vertices count 0xD05. We measure its size, divide it by 2, and get the indices count: 0x8022 / 2 = 0x4011 (16401). Now let's get the indices loaded:

image.thumb.png.701ab6d924e4d9f750fac5040845d06c.png

Looks OK, except for some extra faces. Note that our current vertices count is 2686 out of 3333, which indicates that there're still 647 vertices left not displayed, and that their start offset of the vertices is different from the one we're using now:

image.png.749ad64277481f2df04b70521821e398.png

 

You can grope around for the proper indices count of submesh1 by decreasing the amount and then check the result. But I'm not going to do it that way.

We notice that the max vertex index is 2686 (0xA7E), which is larger than the remaining 647 (0x287).
So the max index no doubts equals the vertex count of submesh1, and the remaining 647 is the one of submesh2.
Now we're going to find the correspond indices counts for each submeshes according to the vertices counts we have.

We don't know whether the file will use long or short type to store the counts, so we just search backward from the start of the vertices for the value as short, which is 0A 7E.
And we actually found it right ahead of the vertices buffer:

image.png.18d5393a6ce011b61288ea14a84f2da1.png

And we can figure out the structure of this vertices header at once:

... 				Face Buffer
01					LOD ID?
00 02 70 F0		Vertices Size
00 00 00 02		Submesh Count
00 00 00 00		First Submesh's Starting Vertex Index
00 00 0A 7E		First Submesh's Vertices Count
00 00 0A 7E		Second Submesh's Starting Vertex Index
00 00 02 87		Second Submesh's Vertices Count
00 00 00 07		Vertices Element IDs Count (the following 7 4-byte sequences are the IDs). There'll be the same amount of elements in a vertex structure.
... Face Buffer 01 LOD ID? 00 02 70 F0 Vertices Size 00 00 00 02 Submesh Count 00 00 00 00 First Submesh's Starting Vertex Index 00 00 0A 7E First Submesh's Vertices Count 00 00 0A 7E Second Submesh's Starting Vertex Index 00 00 02 87 Second Submesh's Vertices Count 00 00 00 07 Vertices Element IDs Count (the following 7 4-byte sequences are the IDs). There'll be the same amount of elements in a vertex structure.

image.png.1b95427e8b851ecf57a67e7b6d12a694.png

00 00 80 22		Face Buffer Size
00 00 00 02		Submesh Count
00 00 00 00		First Submesh's Starting Index
00 00 34 0B		First Submesh's Indices Count
00 00 34 0B		Second Submesh's Starting Index
00 00 0C 06		Second Submesh's Indices Count
00 00 00 01		Indices Element IDs Count (the following sequence 00 01 02 15 is the ID)
So now we got both submesh's indices counts: 0x340B (13323) for submesh1, 0xC06 (3078) for submesh2. We sum them up and get 16401, which is exactly the total
indices count we filled in Hex2Obj. Let's validate it:

image.thumb.png.0a8732c86bb7f84f8483d8da9c4066c8.png

So our guess is correct.

Now it's time to handle the UVs.
As you may recall, the UVs are ahead of the vertex coordinates, so we can't use its position relative to the coordinates to access to them.
Instead, we use the obsolute offset of the UVs. The UVB size is the same as the vertices as they're under the same structure.
We fill in the blanks with the right info, select HF_UV from the data type rollout, then press the UVs button:

image.thumb.png.eac2b698e962f8cc87c061c2680af31a.png

Now let's save this model as an obj file by navigating to File>SaveAs mesh.

We can even test with submesh2 if we want to. Just need several steps of calculations to obtain the start offsets:

Vertices: 0xE7C7 + 2686 * 48 = 0x2DF67
UVs: 0x2DF67 － 0x4 = 0x2DF63
FI: 0x6764 + 13323 * 2 = 0xCF7A

With the assistance of the calculator of HexEdit we can get the results within a few seconds.

We've already got the counts for submesh2: 3078 indices and 647 verts. So let's see how it goes:

image.thumb.png.4541307282852cbd0fec6f02e22bddd4.png

Everything play as we expected. So far we can already build the model with all these infomation we have, but there're still some remaining bytes in that vertex structure. What are these data? You can actually find the answer from the strings at the front part of the file, which I told you not to pay much attention to:

image.png.28fca61c563c9fbf2357edc830992743.png

But don't get it wrong. The only reason I skipped these strings is for teaching purpose. When you're actually researching a file format, you  would make full use of these info. It'll definitely save you a lot of time.

Up to now, I've shown you how to analyze a model format, and to use Hex2Obj to validate your guess. I've also left you with another nif file (iron_skin_m.nif). See if you can extract the model within on your own.

So, I guess that's all for this part.

 

<<BACK TO INDEX

Like
Quote
michalss
michalssProficient
Administrators
 266
 14
Author
Posted November 7, 2023
Part IV. Analyzing and Reverse Engineering a Game Archive


In Part III we've been able to extract the model from one of the nif files. But these files are orginally packed as a big .xpr archive. So in this part, I'll
show you how to reverse engineering the structure of the entire xpr package. It's more complicated than reversing a model. But that doesn't mean it's difficult.
Just follow my reasoning process.

Download the example xpr file XPR Archive.rar

Let's open it with HexEdit. The first thing I usually do is to measure the size of the whole file. Press the EOF button at the lower left of the calculator
and it says 0x67F000. OK, let's analyze the data.

The first 4 bytes is the file magic: "SMX7", which's the only thing that can verify the archive.

image.png.69327cfd7bb6a62e2a80ecb87715ecac.png

The 3 fields in the green rectangles are easy to figure out, while those in the black frame are still unknown:

image.thumb.png.463e2037bea31b91a03ffcd54f80a1c1.png

Then we measure the size from 0xA0 to where these data ends:

image.png.b91967d38e23d1ca78fdbc201133ca1d.png

It's approximately 0x134F, which's close to 0x1354 from the header. And we can notice that there're a lot of zero bytes coming after and terminates at
offset 0x1800, where the magic "TX2D" starts. So we now know another two fields of the header:

image.thumb.png.6897cb89ac72220b40e364863154f2dd.png

And also the padding size referring to offset 0: 0x800 bytes.

We continue the analysis from 0x1800, and measure the size from here to where this chunk ends. Note that the end offset must be a multiple of 0x800.
So we get it at 0x2800. 0x2800 - 0x1800 = 0x1000, which can be found at the header.

Here at 0x2800 we see another magic: "KFSQ". Again let's measure the size of this chunk. It seems difficult to located where it ends, so we measure it
till its last nonzero byte, which is 0x290155. That perfectly matches with the value 0x290800 at the header.

Let's see how many bytes are left. We jump over 0x290800 bytes from 0x2800, and subtract the current address from the total file size:
0x67F000 - 0x290800 - 0x2800 = 0x3EC000. Can you tell where this value is?
So we're getting closer now:

image.thumb.png.9b9a2fb2f9dfbd51b2acd02465807bf4.png

Now we have to figure out the structure of each chunk. Start with the "TX2D" chunk first. Jump to 0x1800, where we can see a lot of "TX2D" markers.
For convenience of analysis, we need to align them like this:

image.png.fec7ee63da8a5678eee31379ff93e656.png

Let's see how many markers there are: 0x12C / 0x14(20) = 0xF. So the 00 00 00 0F at the header is the count of these markers. Same thing can be applied to the "KFSQ" chunk. Therefore we get almost the entire header reversed.

image.thumb.png.2e6dee34b0faf2935f209cc169f584ac.png

Then we continue our research on the "TX2D" chunk. First we need to have an overall idea of how this chunk is organized:
the "TX2D" Table, a filename Table, then some more alignable data.

Let's try to have a look at the "TX2D" table and see if we can find something.

image.png.2914e5c93ce3fb381b86976f83c0303b.png

We notice that the values in each green frame are all in an increasing order. That means these values could be some offsets. And since they're all minner than the current position, they should be relative to somewhere around.

Then what would these offsets direct to? Of course, the filename table, and the unknown data followed probably, what else?
With some assumptions and validations soon we can figure out the answers:

image.thumb.png.fa673c5071aa0b0b2c025f0f40e96d54.png

All these offsets are relative to where the "TX2D" table begins. While the structure of the texture info header table is like:

image.png.2239649be87616f0c83bce6c81f52351.png

Similarly, we can also reverse the structure of the "KFSQ" chunk. But I'm not going to explore it here. Consider it as a task for practicing.
But in the BMS scripting part, I'll expose you the whole structure of the archive.

Finally, we have reached the end of this manual researching section. Thanks for reading!

 

<<BACK TO INDEX

Like
Quote
2 yr
michalss changed the title to Ultimate Tutorial for Reverse Engineering a Game Model (WIP)
michalss
michalssProficient
Administrators
 266
 14
Author
Posted November 7, 2023
Programming Section 

Part I. Basic BMS Scripting

As you may or may not know, QuickBMS is an extremely powerful tool for archive unpacking. BMS was not originally created by Aluigi. Mr.Mouse (Xentax owner) created Mexscript https://en.wikipedia.org/wiki/MexScript For MultiEx Commander, and he compiled the script into Binary MultiEx Script for the program to use. Aluigi then created the command-line tool QuickBMS, first supporting Mexscript vanilla, but gradually expanding on it. 


QuickBMS Homepage

This tutorial will not explain you the usage of the QuickBMS commands, because there's already been a highly detailed explanation in the QuickBMS document.

The following division is not necessarily correct.

Controlling Statements:

Debug [Mode]
CleanExit
Append [Direction]
File Attributes Statements:

IDString [FileNum] String
Endian Type [VAR]
ComType ALGO [Dict] [Dict_Size]
Searching and Jumping Statements:

FindLoc VAR Type String [FileNum] [ERR_Value] [End_OFF]
GoTo Offset [FileNum] [Type]
Padding VAR [FileNum] [Base_OFF]
Reading Operations:

Get VAR Type [FileNum]
GetCT VAR Type Char [FileNum]
GetDString VAR length [FileNum]
Writing Operations:

PutVARChr VAR Offset VAR [Type]
Log Name Offset Size [FileNum] [Xsize]
Clog Name Offset Zsize Size [FileNum] [Xsize]
Mathematical/Assignment Operations:

Math VAR OP VAR
XMath VAR INSTR
String VAR OP VAR
Set VAR [Type] VAR
SavePos VAR [FileNum]
File Accessing Statement:

Open Folder Name [FileNum] [Exists]
Judgement Statement:

If VAR COND VAR [...]
...
[Elif VAR COND VAR]
...
[Else]
...
EndIf
Circular Statements:

Do
...
While VAR COND VAR
For [VAR] [OP] [Value] [COND] [VAR]
...
Next [VAR] [OP] [Value]
 

If you've read all the usages of the above commands, we can start our demonstration now.

The game we're deaing with is still Marvel Avengers: Battle for Earth. But before we start writing our BMS script, we have to know the full structure of the
archive we're going to unpack. And this'is the overall format structure of the xpr archives from this game:

Bytes		Padding(0x800)

for i = 0 < TexFileCount
{
	Long		Magic("TX2D")
	Long		TexInfoHeaderOffset(Relative)
	Long		TexInfoHeaderSize
	Long		TextureFilenameOffset(Relative)
	Long		TextureFilenameEndOffset(Relative)
}

Long		Null

for i = 0 < TexFileCount
{
	String		TextureFilename(Null-terminated)
	Byte		Null
}

for i = 0 < TexFileCount
{
	0x40-byte	TexInfoHeader
	{
		0x20-byte	Ignore
		Long		TextureDataOffset
		0x1C-byte	Ignore
	}
}

Bytes		Padding(0x800)

for i = 0 < kfFileCount
{
	Long		Magic("KFSQ", "KFMT", "SCNG")
	Long		kfDataOffset(Relative)
	Long		kfDataSize
	Long		kfFilenameOffset(Relative)
	Long		urnOffset(Relative)
}

Long		Null
 
for i = 0 < kfFileCount
{
	String		kfFilename(Null-terminated)
	String		urn(Null-terminated)
}

for i = 0 < kfFileCount
{
	Bytes		kfFile
	{
		Long		CompressionFlag
		Long		UnzipSize
		Bytes		CompressedStream
	}
}

Bytes		Padding(0x800)

for i = 0 < TexFileCount
{
	Bytes		RawTextureData
}

 

The second step is to construct a simple algorithm for unpacking all the assets in the target archive:

1. read the variables from the file header;
2. locate to each chunk according to the above variables;
3. read the info table of each chunk;
4. extract all the assets in each chunk according to its coresponding info header.

Now let's translate this algorithm into a BMS script:

Type		Specification

Long		0x534D5837/"SMX7"
Long		TexTableOffset
Long		TexTableSize
Long		kfDataSize
Long		RawTextureDataSize
Long		CompressionFlag(XMEMLZX Compressed)
Long		TexFileCount
Long		kfFileCount
Long		Magic("USER")
Long		xblockFileOffset
Long		xblockFileSize
Long		xblockFileNameOffset
Long		xblockFileUrnOffset
Long		Null
String		xblockFileName(Null-terminated)
String		xblockFileName(Padding to 0x10)

Bytes		xblockFile
{
	Long		CompressionFlag
	Long		UnzipSize
	Bytes		CompressedStream
}

Bytes		Padding(0x800)

for i = 0 < TexFileCount
{
	Long		Magic("TX2D")
	Long		TexInfoHeaderOffset(Relative)
	Long		TexInfoHeaderSize
	Long		TextureFilenameOffset(Relative)
	Long		TextureFilenameEndOffset(Relative)
}

Long		Null

for i = 0 < TexFileCount
{
	String		TextureFilename(Null-terminated)
	Byte		Null
}

for i = 0 < TexFileCount
{
	0x40-byte	TexInfoHeader
	{
		0x20-byte	Ignore
		Long		TextureDataOffset
		0x1C-byte	Ignore
	}
}

Bytes		Padding(0x800)

for i = 0 < kfFileCount
{
	Long		Magic("KFSQ", "KFMT", "SCNG")
	Long		kfDataOffset(Relative)
	Long		kfDataSize
	Long		kfFilenameOffset(Relative)
	Long		urnOffset(Relative)
}

Long		Null
 
for i = 0 < kfFileCount
{
	String		kfFilename(Null-terminated)
	String		urn(Null-terminated)
}

for i = 0 < kfFileCount
{
	Bytes		kfFile
	{
		Long		CompressionFlag
		Long		UnzipSize
		Bytes		CompressedStreamType		Specification

Long		0x534D5837/"SMX7"
Long		TexTableOffset
Long		TexTableSize
Long		kfDataSize
Long		RawTextureDataSize
Long		CompressionFlag(XMEMLZX Compressed)
Long		TexFileCount
Long		kfFileCount
Long		Magic("USER")
Long		xblockFileOffset
Long		xblockFileSize
Long		xblockFileNameOffset
Long		xblockFileUrnOffset
Long		Null
String		xblockFileName(Null-terminated)
String		xblockFileName(Padding to 0x10)

Bytes		xblockFile
{
	Long		CompressionFlag
	Long		UnzipSize
	Bytes		CompressedStream
}

Bytes		Padding(0x800)

for i = 0 < TexFileCount
{
	Long		Magic("TX2D")
	Long		TexInfoHeaderOffset(Relative)
	Long		TexInfoHeaderSize
	Long		TextureFilenameOffset(Relative)
	Long		TextureFilenameEndOffset(Relative)
}

Long		Null

for i = 0 < TexFileCount
{
	String		TextureFilename(Null-terminated)
	Byte		Null
}

for i = 0 < TexFileCount
{
	0x40-byte	TexInfoHeader
	{
		0x20-byte	Ignore
		Long		TextureDataOffset
		0x1C-byte	Ignore
	}
}

Bytes		Padding(0x800)

for i = 0 < kfFileCount
{
	Long		Magic("KFSQ", "KFMT", "SCNG")
	Long		kfDataOffset(Relative)
	Long		kfDataSize
	Long		kfFilenameOffset(Relative)
	Long		urnOffset(Relative)
}

Long		Null
 
for i = 0 < kfFileCount
{
	String		kfFilename(Null-terminated)
	String		urn(Null-terminated)
}

for i = 0 < kfFileCount
{
	Bytes		kfFile
	{
		Long		CompressionFlag
		Long		UnzipSize
		Bytes		CompressedStream
	}
}

Bytes		Padding(0x800)

for i = 0 < TexFileCount
{
	Bytes		RawTextureData
}
	}
}

Bytes		Padding(0x800)

for i = 0 < TexFileCount
{
	Bytes		RawTextureData
}
The second step is to construct a simple algorithm for unpacking all the assets in the target archive:

1. read the variables from the file header;
2. locate to each chunk according to the above variables;
3. read the info table of each chunk;
4. extract all the assets in each chunk according to its coresponding info header.

Now let's translate this algorithm into a BMS script:

next i
## read texture names ##
for i = 0 < TexFileCount
	math TexNameOffset[i] + TexTableOffset	# convert TexNameOffset to obsolute offset
	goto TexNameOffset[i]					# jump to offset to texture filename
	getct TexName[i] string 0x2E			# skip the file extension ".bmp"
	string TexName[i] | \					# wipe the drive letter
	string TexName[i] + ".bfe"				# we use custom extension to prevent confusion
next i
## write texture info header to file ##
for i = 0 < TexFileCount
	math InfoHeaderOffset[i] + TexTableOffset	# convert InfoHeaderOffset to obsolute offset
	goto InfoHeaderOffset[i]					# jump to offset to texture info header
	goto 0x20 0 SEEK_CUR						# skip 0x20 bytes
	get RawTexOffset[i] long					# read offset to raw image data
	math RawTexOffset[i] & 0xFFFFFF00			# the last byte is used as a format flag, so we need to set it to zero 
	log TexName[i] InfoHeaderOffset[i] 0x40		# the InfoHeaderSize = 0x34, but we use 0x40 for sake of alignment
next i
## initialize data size for each texture ##
set j long 0									# initialize global cyclic variable
for i = 1 < TexFileCount
	xmath j "i - 1"								# assign (i - 1) to j
	set TexSize[j] RawTexOffset[i]				# initialize TexSize[j] as RawTexOffset[i]
next i
xmath j "i - 1"									# assign (i - 1) to j, where current i = TexFileCount - 1
set TexSize[j] RawTexDataSize					# we have to initialize the last TexSize separately

## calculate data size for each texture and write data to file ##
append											# enable append mode as we've written the info header to these files
for i = 0 < TexFileCount
	math j = i									# synchronize j with i
	math TexSize[j] - RawTexOffset[i]			# calculate data size for texture
	math RawTexOffset[i] + TexDataOffset		# convert RawTexOffset to obsolute offset
	log TexName[i] RawTexOffset[i] TexSize[j]	# write raw texture data to file
next i
append											# disable append mode when we don't need it anymore

### handling KF files ###
set KfmTableOffset long TexTableOffset			# initialize KfmTableOffset as TexTableOffset
math KfmTableOffset + TexTableSize				# calculate KfmTableOffset
goto KfmTableOffset								# jump to KfmTableOffset
## read Kfm table ##
for i = 0 < KfmFileCount
	get Magic long								# "KFSQ" "KFMT" "SCNG"
	get KfmDataOffset[i] long
	get KfmDataSize[i] long						# size of Kfm asset
	get KfmNameOffset[i] long					# offset to Kfm filename
	get urnOffset long							# offset to urn string, which's useless though
next i
## read Kfm filenames ##
for i = 0 < KfmFileCount
	math KfmNameOffset[i] + KfmTableOffset		# convert KfmNameOffset to obsolute offset
	goto KfmNameOffset[i]						# jump to KfmNameOffset
	get KfmName[i] string						# read KfmName
	string KfmName[i] | \						# wipe the drive letter
next i
## extract Kfm assets ##
for i = 0 < KfmFileCount
	math KfmDataOffset[i] + KfmTableOffset		# convert KfmDataOffset to obsolute offset
	goto KfmDataOffset[i]						# jump to KfmDataOffset
	get CompressionFlag long					# read CompressionFlag
	get UnzipSize long							# decompressed size of Kfm asset
	savepos KfmDataOffset[i]					# save current address as offset to Kfm stream
	if CompressionFlag == 1						# data is compressed
		math KfmDataSize[i] - 8					# subtract 8 bytes from KfmDataSize
		clog KfmName[i] KfmDataOffset[i] KfmDataSize[i] UnzipSize	# write data to file
	else
		log KfmName[i] KfmDataOffset[i] UnzipSize					# write data to file
	endif
next i
You can copy and paste the above code into a text file and run it through QuickBMS with the xpr archive I provided.

Of course, there can still be some optimizations, like using shared variable names, etc. But to avoid reducing readability, I'll leave it just like that.

So this is the end of the BMS scripting lesson.