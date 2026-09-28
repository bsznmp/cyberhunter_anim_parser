[Tutorial] How to restore hashed filenames from archives (a.k.a How to restore original strings from hash values, a.k.a. How to get filenames for Obscure 2 HVP archives)


Introduction:
This tutorial aims to teach you how to recover „lost” filenames hidden by developers behind a hash function.
Some developers uses custom algorithms to hide filenames, others uses standard/well-known algorithms.
Good example for this tutorial I’ve found recently is CRC32 checksum used as a hash function in game „Obscure 2” for PC.
I will refer to this example while describing methods in this tutorial.
Hash values are stored inside HVP archives in directory section, so following the examples would require a working copy of the game.

Here are some useful links to get you started:

CRC32 –> https://en.wikipedia.org/wiki/Cyclic_redundancy_check
Hash –> https://en.wikipedia.org/wiki/Cryptographic_hash_function
HVP file format –> http://wiki.xentax.com/index.php/Obscure_2_HVP
Obscure 2 Tools –> https://github.com/bartlomiejduda/Tools/tree/master/NEW%20Tools/ObsCure%202

Below I will describe all methods that can be used to restore original filenames.

But you may ask – why do I need this?
Of course it is easier to edit game files if you know real filenames, that’s an obvious reason. You also need filenames to uncover game’s secrets. Like if you know that some file is called „debug_menu.bin”, then you can be 100% sure that this specific file can have some logic for displaying debug menu in game etc. etc. Knowing filenames can be also useful for comparing game versions for different platforms (for example „Obscure 2” is available on PC, PSP, PS2 and WII – and each platform has unique set of hash values!)

FOLLOW THIS TUTORIAL ONLY AT YOUR OWN RISK!
I AM NOT RESPONSIBLE FOR ANY DAMAGES THAT YOU WILL ENCOUNTER AFTER READING THIS TUTORIAL!
THIS TUTORIAL IS FOR EDUCATIONAL PURPOSES ONLY! DON’T USE IT TO CRACK PASSWORDS!

1. Creating a hook + playing a game with injected hook
This method may be a little complicated, so if you’re not a programmer and you don’t know how to do software reverse engineering, I would recommend to skip to other methods.

But if you know something about DLL injection already, you should always start with this method as it seems to be most effective one 🙂

So what you should know about this method? Main goal is to hook hash function in memory, then play a game with this hook injected.
I won’t be describing in details how to create such hook, because there are several tutorials about that already.

If you’ll allocate console window, you should see your dumped strings there like this:

[image]

Using hooks you can inject any C++ code that can be compiled, so you can dump all hashes to some output file on your hard drive and then process them with some scripts. 😉

Here is a good example of a hook –> LINK

2. Guessing
This great method requires from you no programming knowledge at all. To guess some filenames, you can use for example Hex Editor and CyberChef.

So in Obscure 2, there is an file format with ZWO extension, I believe it is some kind of 3D Model format – but it is not important.
After loading one of these files in hex editor, you can see something like this in header:

[image]

You can see „crank2_ccw” name. I looked in other similar files earlier in hex editor, so I could definitely tell that this name in most cases should be exact match with the real filename (without suffix and an extension).

So after adding suffix and an extension, I’ve ended up with this filename –> „crank2_ccw_pc.zwo” which was exact match for one of the hashes in HVP archive.

When you have such string, you can go to CyberChef website https://gchq.github.io/CyberChef/
and check your result:

[image]

If the hash is correct, you can add it to your hash list.

3. Exe dump
This method requires you to use „Strings” tool from sysinternals –> https://learn.microsoft.com/en-us/sysinternals/downloads/strings

Once you’ve downloaded it, you can dump all strings from any file. You will get best results when dumping strings from EXE and DLL files.
Here is an exmaple from „Obscure 2.exe” file.

[iamge]

So one of the filenames that can be recovered this way is „circuit.zwo„.

4. Memory dump
This is similar method to „Exe dump”, but in this case you can dump a block of memory from running process.
To use this method, you need to run the game and then run some tool that will handle memory dump for you.

You can use for example TotalDump –> LINK

5. Process monitor – „NAME NOT FOUND”
This method only applies to games that are capable of reading loose files outside of the main archives.
You can download Process monitor https://learn.microsoft.com/en-us/sysinternals/downloads/procmon
and then set up filters to show you only failed read operations:

[image]

So as you can see, you can recover „m_border.bmp” filename (and many others) using this method.

6. Hashcat
Hashcat is well known „password recovery” utility. You can use several types of attack when using this tool.

Here is an example script for recovering CRC32 hashes –> LINK
For CRC you can encounter many collisions so it is important to use „–keep-guessing” option.

All results will be stored in „hashcat.potfile” file.

Here is an example result for „videosps” string:

[image]

7. Hooking with Frida
This method is very similar to DLL Injection introduced at the beginning of this article. But instead of writing your own DLL hook, you can use Frida API and input script written in javascript to do what you want.

To use frida, you have to install Python first https://www.python.org/downloads/
Then you have to install frida with command below:

pip install frida
Then you have to go to game’s directory and run frida from there like this:

frida -f Obscure2.exe -l "C:\Users\UserName\Desktop\obscure2_frida_hook.js"
Good example of working hook for „Obscure 2” can be found here –> LINK

Final result should look like this:

[image]

Conclusion:
And that’s all methods for this tutorial. I hope that you’ve learned how to proceed when you have „lost” your filenames and you’ll want to recover them. 😉
