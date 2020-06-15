# condorv2-tile

 A gimp plugin which will split source terragen tiles into a 4x4 grid with files saved as  tCCRR.dds for direct use in Condor Landscapes.



This plugin is more-or-less a combination of ofn-tiles plugin and the .dds exporter from /solidsnake

It is used to process a source folder of terragen named image files - CCRR.png - and will split each terragen file into 16 sub tiles (4x4 grid) - and export each as a .dds file named appropriately for use Condor V2.

Notes:

* Terragen tile files must use the condor tile naming scheme of CCRR.png - with CC being the column number (00 is right most column) and RR being the row number (00 being the bottom most row). I know, this is weird, but it is the way Condor terragen tiles are labeled. If a file is encountered that is not labeled like this, it will be skipped.

* Theoretically, any image format may be used, but currently only .png with alpha layer has been tested.
If the .png has an alpha layer - it will be used in the .dds file for the water layer.

* Terragen tile files must have a width and height that are equal (square image) - and also must have a width/height that is a multiple of 4 - as the terragen tile is split into a 4x4 grid. If these conditions are not met, that image is skipped and the next image in the source folder is processed (i.e., you can have other types of images in the source folder, but it is probably best to keep your source folder just for terragen files you need to process.)

* Terragen tiles are not limited to 8192 width/height - I have tested with 16384 width/height and they work just fine.

