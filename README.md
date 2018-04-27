# OpenKal Parser Collection
A collection of KalOnline data parsers and Blender add-ons written in Python.


## Installation
The data parsers require a Python 3.5 environment or newer with NumPy.

The Blender add-ons require Blender 2.79.
Start by creating an empty script directory.
Next, [make it available](https://docs.blender.org/manual/en/dev/preferences/file.html) to Blender.
Download and extract the repository zip archive.
Copy the `modules` and `addons` directories into the script directory.
Finally, restart Blender and [enable](https://docs.blender.org/manual/en/dev/preferences/addons.html) the OpenKal add-ons.
The add-ons should now be accessible via the import menu.


## Notes
* Import

  A complete model is often split into multiple files.
  To import multiple files into a single object, simply import each file separately using the same object name.
  In general, an animation can only be imported when the corresponding armature was already imported.
  Importing non-matching armature and animation pairs will result in an incomplete and undefined object.

* Textures

  The Blender add-on automatically imports textures.
  Only Direct Draw Surface (DDS) images can be imported.
  In other words, all GTX images need to be converted.
  Filenames and directories must be lowercase.
  The original directory structure should not be changed.

* Completeness

  The Blender add-on imports almost everything from a GB file into Blender.
  This includes armatures, meshes, materials, textures, animations and collision meshes.
  It does not import linked animation events such as sound or particle effects.
  However, everything is loaded into the internal GB structure.


## Progress
- [x] KSM
- [x] KCM
- [x] OPL
- [x] ENV
- [ ] MAP
- [X] DAT
- [X] GTX
- [X] GB
