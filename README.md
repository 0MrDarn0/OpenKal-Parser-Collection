# OpenKal Parser Collection
A collection of KalOnline data parsers and Blender add-ons written in Python.


## Installation
The data parsers require a Python 3.6 environment with NumPy.
The Blender add-on requires Blender 2.79, but other versions might work as well.
Please note, some Blender installations do not provide NumPy and require it to be installed separately.

The Blender add-on can be installed like any other regular Blender add-on.
First, create an empty directory.
Next, [make it available](https://docs.blender.org/manual/en/dev/preferences/file.html) to Blender as a script directory.
Download and extract the repository zip archive.
Copy the `modules` and `addons` directories into the previously created directory.
Finally, restart Blender and [enable](https://docs.blender.org/manual/en/dev/preferences/addons.html) the OpenKal add-on.
The add-on should now be accessible via the import menu.


## Blender Add-On
* Import

  A complete model is often split into multiple files.
  To import multiple files into a single object, simply import each file separately using the same object name.
  In general, an animation can only be imported when the corresponding armature was already imported.
  Importing non-matching armature and animation pairs will result in an incomplete and undefined object.

* Textures

  The Blender add-on automatically imports textures.
  Currently, DDS, PNG and TGA images can be imported.
  In other words, all GTX images need to be converted.
  All paths and names must be lowercase on case-sensitive systems.
  The original directory structure should not be changed, since not all paths are relative.

* Completeness

  The Blender add-on imports almost everything from a GB file into Blender.
  This includes armatures, meshes, materials, textures, animations and collision meshes.
  It does not import linked animation events such as sounds or particle effects.
  However, everything is read into the internal GB structure.
  The export is not implemented.


## Incorrect OPL File
The older clients provide an incorrect OPL, namely n_031_035.
Parsing it as is will cause an exception to be raised.
The correction includes the actual index correction as well as the new checksum.
It can be applied using a HEX editor.

Erroneous n_031_035 data:
```
00000000  69 15 55 1c 00 00 00 00  1f 00 00 00 23 00 00 00
00000010  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
00000020  07 00 00 00 ec 02 00 00  28 00 00 00 44 41 54 41
```

Correct n_031_035 data:
```
00000000  7b a3 a9 9d 00 00 00 00  1f 00 00 00 23 00 00 00
00000010  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
00000020  07 00 00 00 e4 02 00 00  28 00 00 00 44 41 54 41
```
