# inkscape-import-clipart

> Inkscape extension that allows import graphics from a selection of internet sources

https://github.com/lukaszjablonski/inkscape-import-clipart/

It is a graphical user interface allowing searching different sources and inserting of svg and raster images into the current document.

This is a fork of [Inkscape Extras sub project repository](https://gitlab.com/inkscape/extras/inkscape-import-clipart). For credits see [Contributors](https://github.com/lukaszjablonski/inkscape-import-clipart/graphs/) and/or source code in `sources` directory. 

This repository is meant to provide additional sources on top of already implemented ones and necessary changes to the source code of the original extension.

## Sources

Shipped with [Inkscape 1.2](https://wiki.inkscape.org/wiki/Release_notes/1.2) and later:
- [Bioicons](https://bioicons.com/) `bioicons`
- [Inkscape Comunity](https://inkscape.org/gallery/) `inkscape-web`
- [Open Clipart Library](https://openclipart.org/) `ocal`
- [Reactome](https://reactome.org/) `bioreactome`
- [Wikimedia Commons](https://commons.wikimedia.org) `wikimedia`

Added in this repository:
- [SciDraw](https://scidraw.io/) `scidraw` ⚠ [see details](https://github.com/lukaszjablonski/inkscape-import-clipart/compare/8d2948c..33da181)

New sources can be added at any time. They should include an icon and a python file with the same name. Sources should allow the user to search and insert resources from the target website or platform.

Please see existing python files for examples.

## Install

Since "Import Web Image" (Clipart Importer; `inkscape-import-clipart`) is shipped with [Inkscape 1.2](https://wiki.inkscape.org/wiki/Release_notes/1.2) and later copying only new sources implemented in this repository should be enough.

To use only selected sources:
- On Windows copy selected `sourcename` files (i.e., `sourcename.py` and `sourcename.svg`) to `C:\Program Files\Inkscape\share\inkscape\extensions\other\clipart\sources`, where `C:\Program Files\Inkscape\` is Inkscape install location

NOTE: Sources labelled with ⚠ require modified extension core source code! To identify modified files refer to "see details" next to label.
