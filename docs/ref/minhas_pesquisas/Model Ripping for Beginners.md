## Start:

I've finally written a (hopefully) complete, in-depth tutorial on ripping and exporting .BRRES format models and getting them ready for submission. This guide walks you through the process of extracting models out of ISO (game) files using the Dolphin emulator, exporting models with BRRES Viewer and Noesis, and more so that anyone who would like to start ripping models, but aren't sure where to start can learn. Hopefully my instructions are easy to follow, I tried to be as detailed as possible. If you have any problems/questions about anything in this guide, then feel free to ask me by either PM-ing me or posting in this thread. Have fun with the wonderful .BRRES format! (Note: Whenever I post about updates made to the guide, everything that is changed will be in bold.)

## Main guide:

First off, the Wii is the easiest because so many games use the same format and such. And second, the easiest thing to do first is by far .BRRES format models. Here's what you'll need:

1: BRRES Viewer (get it here, and you can find an updated list of games that use .BRRES format here)
2: Noesis (this is the easiest way, you don't have to mess with the model at all usually. Get it here)
3: A text editor (Notepad ++ is recommended because of all the great features it has, but you can just use Notepad if you like. Get Notepad ++ here)
4: Icon Maker V3b (for making icons and previews so that your model will be uploaded faster. Read further for usage help), you can get it here

And that's about it for equipment. Now onto instructions. It's quite easy after you've done a few of them.

Start off by opening BRRES Viewer and browse for the model you want and open it. Now you should see this tall window on the left, listing the model(s), textures, palettes, animations and etc.. This is called the file tree, and will be referred to as such from now on. You can press the enter key to center the model so it won't be on top, or use shift to move it back to its initial position. But for now you want to go to File > Export All Files. You will see a small window appear. Click the Textures dropdown and select PNG (you can also right-click on each texture individually and select Export (then choose the directory you want them to go) to make sure you get them all, but this is tedious). Leave the Models dropdown as it is, as you want to export all your models in .MD5 format.* You should click the Animations dropdown and select "(do not export)" if you don't want to include animations in your submission (you can include them if you want but most people don't and it isn't required). Very important: Make sure you check the "Create one folder for each brres file" box when exporting multiple files so that the files will not conflict and get mixed up with eachother. Now you have to go into the folder that had the BRRES file of the model you just exported. There will be a new folder named "exported". You can pull that out and put it somewhere else. You should now export each model again as a .OBJ. However, it seems that when you click "Export All Files" and choose to have your models exported as .OBJ, it does not export the .MTL file with it (which tells the model which textures go where), thus the model loses its texture mapping. The solution to this, is to double-click on the model (you must be actually viewing the model for the "Export" command to work) you want to export in the file tree, and then go to Model > Export > OBJ. Keep in mind that this will not export the textures with it, so if you don't already have them, go to Export All Files again, make sure the textures drop down is set to PNG, and pick "Do not export" for the other two (if you have multiple models loaded, don't forget to check "Create one folder for each BRRES file" or the textures will be all mixed up!). However since you already exported them as .MD5 first (or at least you should have), you should have them already.

*IMPORTANT NOTE ABOUT THE .MD5 FORMAT: When exporting in .MD5, always check the export to see if it came out right when you open it in Noesis. I don't know if it's because Noesis doesn't always properly convert it, or BRRES Viewer does not always export .MD5 correctly, but sometimes the model will mess up. If the model does mess up, you should be able to see it in Noesis (remember, even if the model looks fine on the outside, the model's bones might have gotten mangled during the export, so click the red skeleton icon on the bottom to view the model skeleton. If the bones look okay to you then proceed to the next steps). This isn't really a common problem AFAIK, but if it happens, use .PSK.

For Blender users, there is a way to get a working .MTL file if you export to .OBJ with Noesis. Find out how here. However since it's better to export .OBJs from BRRES Viewer, this guide is somewhat obsolete. Only use this method if you are for some reason unable to export a .OBJ from BRRES Viewer.

Now open Noesis and load up your new MD5/PSK. It should appear like this. Now you go to File > Export, and you'll see a new window. In the "Main output type" dropdown, first select .DAE COLLADA. Now make sure you check "Flip UV's" on the right so that the textures will load properly in modeling programs like Blender (always do this for each and every export). Now just click OK, then when it's done click Done. I always export it again as .SMD format as well, so I'd suggest that, as it makes your submissions even more useful for the end users. (Also, as a note, if you happen to open your DAE or SMD in Noesis again after you export it you'll see that the textures look weird, but don't worry as that's just from Noesis having flipped the texture UV's and is perfectly normal.)

NOTE: Dazz wrote some VERY helpful instructions below regarding batch exporting + conversion and some very simple yet extremely time-saving tricks below that I somehow forgot to include in this guide. Here they are below:

### Spoiler:

Dazz Wrote:
[spoiler="Batch convert with BRRES Viewer"]
-Batch convert with BRRES Viewer-
Following Mighty Jetters tutorial written above, you can actually convert several models all at the same time, which will make submitting a full game's contents a whole lot easier.

First, in BRRES Viewer, open all the files you want to convert. You can select multiple from the open command, so open a whole bunch by select them all and hitting open - NOT ONE AT A TIME THAT WOULD TAKE YEARS.
[Image: Qdj1b.jpg]

Then select File > Export All Files...
[Image: ucSNR.jpg]

A little window should pop up with a bunch of drop downs. Depending on how you plan to do everything, you can select various options. This screenshot shows the way I opt to do things, as it makes mass converting a lot easier...
[Image: 8An9b.jpg]

Hit OK, and leave the window - it might not work if you're loading absolutely thousands of models, so maybe do this is a few times in batches of whatever works best for your computer.
The windows should appear to do things - just leave it. The bar at the top of the window will read "[Writing...]" until it is complete, at which point it will disappear.
Your converted files will all appear in a folder called "exported" in the same folder as the brres files.
[Image: R5FXV.jpg]

Now the only problem is that all of your files are in the same folder - which is a bastard. Mainly when the textures are named randomly compared to the model's filenames. But if you select to give each brres file its own folder on that pop up window, that wouldn't happen...
There is a reason to have them all in the same folder though, if you want to batch process using Noesis.

### Batch convert with Noesis:

-Batch convert with Noesis-
Now open up Noesis, and check out your folder!
Make sure everything is working alright, by double clicking a couple models just to see they display correctly. You never know.
[Image: uHvWX.jpg]

Now go to Tools > Batch Process
[Image: rSUjH.jpg]

And now a window like this should pop up!
[Image: MpdcQ.jpg]

You can enter the files that you want the application to pick up, and what you want it to dump them out as. Luckily, because you chose to export the previous textures as .png, this will do the same thing.
Then you have to enter "-flipuv" in the additional parameters, AND DELETE WHAT IS ALREADY IN THERE, in order for the textures to appear correctly.
Select "folder batch" and then select the folder of .MD5 files!
Hit ok, and it should look something like this:
[Image: NhhCh.jpg]

Click OK, and it'll start to process the conversion. Once it says that conversion is complete, you can then change the obj output extention to anything else, so now do "smd" (You also have to reselect the folder with the folder batch button, or it will just convert to obj again) and hit OK, wait for that to finish, and then "dae" (and once again, select the folder again) and OK.
Once you're all done converting, you can click cancel to now get rid of that window.

And there you go, you now have a folder filled with everything converted...
[Image: SmF8r.jpg]

### Batch Edit .dae Files:

-Batch Edit .dae Files-

Now you have to edit all of the .dae files, so that the textures will load properly!
This is super fun to do, so trust me - open up Notepad++, and drag alllll of the .dae files into it. (If you sort the window by type, it makes it much easier to select all the .dae files)
[Image: 62jzC.jpg]

Select Search > Find in All Files (CTRL+H)
[Image: lXQUJ.jpg]

Now a window like this will pop up
[Image: 5fOG1.jpg]

You want to find all the giberish you want to have removed from those texture lines (read MJ's tutorial for more explaination) - copy & paste the directory (example: "C:/Users/Computer Name/Desktop/Models") from the texture path in the .DAE file you are editing. [Edited by Mighty Jetters to be more clear]
And since you want it replaced with nothing at all, you just leave "Replace with:" blank. Then hit "Replace all in all opened documents"
[Image: 95d7Q.jpg]
It should then say that it has replaced a tonne of occurances!
[Image: np7xR.jpg]

Now it's not over - you need to add .png on the end. For this, it's a lot more effort, because you need to do this slowly. Basically, put this into your replace window:
[Image: M2ONy.jpg]

And hit "find next" - then replace. Do this for all the entries of textures, and STOP AS SOON AS THAT IS DONE. The text will jump a lot when you're done - and it should highlight the </init_from> after "Image" - this is your stop marker.
Save, and close that .dae - and that is finished! Continue this process for the rest...
This is the boring bit - but it's the final step! Once all of those are done, you're done! Loads of fully working .dae files Smile

Now stick everything into the right folders (effort) and zip them up, and submit them!


## Next you have to modify your .DAE:

Now after you save that, you're done aside from making the preview and icon. Icon Maker V3b isn't much different from V1, you can just pick between sprite icons, model icons and previews, and texture icons (click "Load Image" or Ctrl + L to import images. With the newest revision, you can now load or drag and drop your saved model renders in the Icon Maker and they'll keep their transparency!).
