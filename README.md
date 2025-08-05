# Gallium's bitmap font generator
**Generate an accurate TTF or OTF font by vectorizing Minecraft resource pack files.**

## Program Usage
When you launch the program, you’ll see a selection menu where you can choose which step to run.  
Each step requires the output of the previous one, and you will be notified if a step cannot be executed due to missing files.  
The first step requires an internet connection to download assets; the other two only need a connection to install dependencies.  
If you enter step 0, all steps will be executed in order.

```
Welcome to Gallium's bitmap font converter.
What would you like to start with?

Type a number to execute the corresponding step.
  0: Do everything! (Recommended)
  1: Download assets
  2: Make UFO folder
  3: Compile font
  Press enter to exit.
```

## File Arguments
*Coming soon.*

## Custom resource pack
*Instructions on how to use a custom ressource pack are coming soon.*

## Python Dependencies
There are only 2 dependencies, that are automatically installed. 
- `Pillow` for image manipulation *(step 2)*
- `fontmake` to compile the UFO file into a font *(step 3)*
