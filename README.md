# inkscape-import-clipart

> Inkscape extension that allows import graphics from a selection of internet sources

https://github.com/lukaszjablonski/inkscape-import-clipart/

It is a graphical user interface allowing searching different sources and inserting of svg and raster images into the current document.

This is a fork of [Inkscape Extras sub project repository](https://gitlab.com/inkscape/extras/inkscape-import-clipart). For credits see [Contributors](https://github.com/lukaszjablonski/inkscape-import-clipart/graphs/) and/or source code in `sources` directory. 

This repository is meant to provide additional sources on top of already implemented ones and necessery changes to the source code of the original plugin.

## Sources

Already implemented and shipped with Inkscape:
- [Bioicons](https://bioicons.com/) `bioicons`
- [Inkscape Comunity](https://inkscape.org/gallery/) `inkscape-web`
- [Open Clipart Library](https://openclipart.org/) `ocal`
- [Reactome](https://reactome.org/) `bioreactome`
- [Wikimedia Commons](https://commons.wikimedia.org) `wikimedia`

Added in this repository:
- [NIH BioArt Source](https://bioart.niaid.nih.gov/) `bioart` ⛔ [dead API](https://bioart.niaid.nih.gov/api/search/type:bioart%20AND%20neuron)

New sources can be added at any time. They should include an icon and a python file with the same name. Sources should allow the user to search and insert resources from the target website or platform.

Please see existing python files for examples.