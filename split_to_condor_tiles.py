#!/usr/bin/env python
# -*- coding: utf-8 -*-

# GIMP plugin to split a CondorV2 Terragen tile into a 4x4 grid of tiles ready for
# use in a Condor V2 landscape scenery.

# (c) BlueFang 2020
#
#   History:
#
#   v0.1: First published on Github

#   Credits:
#   The splitting of file into tiles was derrived from ofn-tiles gimp plugin
#   The documentation / and how to save to .dds was derrived from /solidxsnake
#   plugins posted on the condorsoaring.com forums


#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This very file is the complete source code to the program.
#
#   If you make and redistribute changes to this code, please mark it
#   in reasonable ways as different from the original version. 
#   
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   The GPL v3 licence is available at: https://www.gnu.org/licenses/gpl-3.0.en.html


import sys,os,os.path,re,glob,traceback,math
from gimpfu import *
from array import *
from random import *

#sys.stderr = open( 'c:\\temp\\gimpstderr.txt', 'w')
#sys.stdout = open( 'c:\\temp\\gimpstdout.txt', 'w')
    
def iterate_tiles(terragen_col, terragen_row):
    column_base = terragen_col * 4
    row_base = terragen_row *4
    for column in range(4):
        for row in range(4):
            yield column+column_base, row+row_base,3-column,3-row


def convert_files(directory, namePattern, saveBMP):
    print 'convert_files for directory'
    print directory

    condor_filename_format = 't{:02}{:02}.dds'

    filedescription = os.path.join(directory, namePattern)
    filelist = pdb.file_glob(filedescription,0)[1]

    tile_col = 0
    tile_row = 0
    workingLayer = None

    try:

        output_dir = os.path.join(directory, 'dds')
        
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
            
        for fname in filelist:

            absname = os.path.abspath(fname)
            root, extension = os.path.splitext(absname)
            basename = os.path.split(root)[1]
            bmp_base_name = basename + '.bmp'
            bmp_file_name = os.path.join(directory,bmp_base_name)
            print 'bmp file path {}'.format(bmp_file_name)

            if len(basename) != 4:
                print 'image file name must be of the format ccrr.png'
                continue

            print 'working on file {}'.format(absname)
            workingLayer = None
            image = pdb.gimp_file_load(absname, absname)
            image.undo_freeze()

            workingLayer = pdb.gimp_layer_new_from_visible(image, image, "tiles")
            image.add_layer(workingLayer, 0)
            width = int(image.width)
            height = int(image.height)
            if width != height:
                print 'image width and height must be the same - skipping to next image'
                continue
            if width % 4:
                print 'image dimensions must be a multiple of 4 - skipping to next image'
                continue

            tile_width = width / 4
            tile_height = height / 4

            cc = basename[:2]
            rr = basename[-2:]

            print 'cc = %s' % cc
            print 'rr = %s' % rr
            
            terragen_col = int(cc)
            terragen_row = int(rr)

            print 'image dimensions = %d, %d' % (width,height)
            print 'tile_width = %d' % tile_width
            print 'tile_height = %d' % tile_height

            print 'iterating through rows and cols'
            step = 1
            for tile_col,tile_row,column,row in iterate_tiles(terragen_col, terragen_row):
                try:
                    filename=condor_filename_format.format(tile_col, tile_row)
                    print 'creating condor tile: %s' % filename
                except KeyError as e:
                    raise Exception('No formatting variable called "%s"' % e.args[0]) 

                # give user some feedback on progress
                updateTxt = 'tile: {:02}{:02} : {} of 16'.format(tile_col, tile_row,step)
                pdb.gimp_progress_set_text(updateTxt)
                pdb.gimp_progress_update(float(step)/float(16))
                
                filename = os.path.join(output_dir,filename)
                tile = workingLayer.copy()
                image.add_layer(tile,0)
                tile.resize(tile_width, tile_height,-column*tile_width,-row*tile_height)

                if os.path.isfile(filename):
                    os.remove(filename)

                pdb.file_dds_save(image, tile, filename, filename, 
                    2, # dxt3 compression
                    1, # mipmaps
                    0, # selected layer
                    2, # format RGBA4
                    -1, # transparency index
                    3, # 3 - triangle, 8 - kaiser mipmap filter
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
                image.remove_layer(tile)
                step += 1

            
            if workingLayer:
                image.remove_layer(workingLayer)

            if saveBMP:
                print 'save bmp option is checked... saving input file as 24bit RGB .bmp'
                saving_image = pdb.gimp_image_duplicate(image)
                saving_drawable = pdb.gimp_image_merge_visible_layers(saving_image, 1)
                # this effectively removes the alpha layer 
                # we have to set it to completely opaque first because
                # GIMP offers no option of just removing the alpha layer
                # when it does a flatten it ALWAYS applies the alpha layer value
                # to the background color - which is the dumbest thing ever
                pdb.gimp_drawable_levels(saving_drawable, 4, 0, 1, 0, 1, 1, 1, 0)
                pdb.gimp_layer_flatten(saving_drawable)

                if os.path.isfile(bmp_file_name):
                    os.remove(bmp_file_name)
                pdb.file_bmp_save(saving_image, saving_drawable, bmp_file_name, bmp_file_name)
                pdb.gimp_image_delete(saving_image)

            image.undo_thaw()
            pdb.gimp_image_delete(image)

    except Exception as e:
        pdb.gimp_message(e.args[0])
        print traceback.format_exc()

    print 'split complete!'


def make_trees(directory, namePattern, hasTree, deciduousAmt, deciduousColor, coniferousColor):
    print 'make the trees'

    try:

        print 'diciduous color ='
        print deciduousColor
        
        filedescription = os.path.join(directory, namePattern)
        filelist = pdb.file_glob(filedescription,0)[1]
        seed()
        output_dir = os.path.join(directory, 'forest')

        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        print 'looping through *.png files'

        for fname in filelist:

            absname = os.path.abspath(fname)
            root, extension = os.path.splitext(absname)
            basename = os.path.split(root)[1]

            deciduous_name = 'b{}.bmp'.format(basename)
            coniferous_name = 's{}.bmp'.format(basename)

            deciduous_path = os.path.join(output_dir, deciduous_name)
            coniferous_path = os.path.join(output_dir, coniferous_name)

            if len(basename) != 4:
                print 'image file name must be of the format ccrr.png'
                continue

            sourceLayer = None

            image = pdb.gimp_file_load(absname, absname)
            image.undo_freeze()

            deciduous_img = pdb.gimp_image_duplicate(image)
            coniferous_img = pdb.gimp_image_duplicate(image)

            deciduous_img.undo_freeze()
            coniferous_img.undo_freeze()

            sourceLayer = pdb.gimp_layer_new_from_visible(image, image, "working")

            width = sourceLayer.width
            height = sourceLayer.height

            deciduous_layer = gimp.Layer(deciduous_img, "deciduous_layer", width, height, sourceLayer.type, sourceLayer.opacity, sourceLayer.mode)
            deciduous_img.add_layer(deciduous_layer, 0)
            pdb.gimp_edit_clear(deciduous_layer)
            deciduous_layer.flush()

            coniferous_layer = gimp.Layer(coniferous_img, "coniferous_layer", width, height, sourceLayer.type, sourceLayer.opacity, sourceLayer.mode)
            coniferous_img.add_layer(coniferous_layer, 0)
            pdb.gimp_edit_clear(coniferous_layer)
            coniferous_layer.flush()

            src_rgn = sourceLayer.get_pixel_rgn(0,0,width,height,TRUE,FALSE)
            src_pixels = array("B", src_rgn[0:width, 0:height])

            b_rgn = deciduous_layer.get_pixel_rgn(0,0,width,height,TRUE,FALSE)
            b_pixels = array("B", b_rgn[0:width, 0:height])

            s_rgn = coniferous_layer.get_pixel_rgn(0,0,width,height,TRUE,FALSE)
            s_pixels = array("B", s_rgn[0:width, 0:height])

            p_size = len(src_rgn[0,0])

            for y in xrange(0, height - 1):
                for x in xrange(0, width - 1):

                    pos = (x + width * y) * p_size
                    src_pixel = src_pixels[pos : pos + p_size]

                    b_pixel = [0,0,0,255]
                    s_pixel = [0,0,0,255]

                    # are we dealing with a non transparent pixel
                    # we only replace non transparent pixels - i.e., the alpha layer
                    # must be used to define where trees live
                    if src_pixel[3] == 255:

                        # if hasTree = 0 - there will be no trees at all
                        if hasTree > 0:

                            # hasTree defines the "chance" that the defined pixel is a tree
                            if randrange(100) < hasTree:

                                # if the pixel has a tree - deciduousAmt defines the chance it is a deciduous tree
                                if randrange(100) < deciduousAmt:
                                    # make deciduous
                                    b_pixel =  deciduousColor
                                # if it is a tree and it is not a deciduous tree, then it must be a coniferous tree
                                else:
                                    # make coniferous
                                    s_pixel = coniferousColor
                        
                        
                    b_pixels[pos : pos + p_size] = array("B", b_pixel)
                    s_pixels[pos : pos + p_size] = array("B", s_pixel)

                    

            # python is weird... cool, but weird...
            b_rgn[0:width, 0:height] = b_pixels.tostring()
            s_rgn[0:width, 0:height] = s_pixels.tostring()

            coniferous_layer.flush()
            coniferous_layer.update(0,0,width,height)
            deciduous_layer.flush()
            deciduous_layer.update(0,0,width,height)

            # this removes the alpha layer from our tree images
            pdb.gimp_drawable_levels(coniferous_layer, 4, 0, 1, 0, 1, 1, 1, 0)
            pdb.gimp_layer_flatten(coniferous_layer)

            pdb.gimp_drawable_levels(deciduous_layer, 4, 0, 1, 0, 1, 1, 1, 0)
            pdb.gimp_layer_flatten(deciduous_layer)

            coniferous_img.undo_thaw()
            deciduous_img.undo_thaw()

            if os.path.isfile(coniferous_path):
                    os.remove(coniferous_path)
            if os.path.isfile(deciduous_path):
                    os.remove(deciduous_path)

            pdb.file_bmp_save(coniferous_img, coniferous_layer, coniferous_path, coniferous_path)
            pdb.file_bmp_save(deciduous_img, deciduous_layer, deciduous_path, deciduous_path)

            image.undo_thaw()
            pdb.gimp_image_delete(image)
            
            

    except Exception as e:
        pdb.gimp_message(e.args[0])
        print traceback.format_exc()


author='bluefang'
year='2020'
exportMenu='<Image>/File/Export/Condor: Split Tiles...'
exportDesc='Split image into 4x4 grid and export each to condor formatted tCCRR.dds file'
openDesc='Split files into 4x4 grid and export each grid to condor formatted .dds file'
whoiam='\n'+os.path.abspath(sys.argv[0])
treeDesc = 'Create bXXX and sXXXX forest files for Condor based on .png input file where the alpha channel defines where trees grow.'

register(
    'split-to-condor-tiles',
    openDesc,openDesc+whoiam,author,author,year,'Condor: Convert and split to .dds tiles...',
    '',
    [
        (PF_DIRNAME,    'directory',    'Directory',   '.'),
        (PF_STRING,     'namePattern',  'Input File Type',   '*.png'),
        (PF_TOGGLE,     'saveBMP',      'Export to BMP',    0)
    ],
    [
        (PF_IMAGE,      'image',    'Opened image', None) 
    ],
    convert_files,
    menu='<Image>/File/Open'
)


register(
    'condor-tree-density',
    treeDesc,treeDesc+whoiam,author,author,year,'Condor: Forest tile creator...',
    '',
    [
        (PF_DIRNAME,    'directory',        'Directory',   '.'),
        (PF_STRING,     'namePattern',      'Input File Type',   '*.png'),
        (PF_SLIDER,     "hasTree",          "Tree Density", 100, (0, 100, 1)),
        (PF_SLIDER,     "deciduousAmt",     "Deciduous Density", 70, (0, 100, 1)),
        (PF_COLOR,      "deciduousColor",   "Deciduous Color", (0.0, 1.0, 0.0)),
        (PF_COLOR,      "coniferousColor",  "Coniferous Color", (1.0, 0.0, 1.0))
    ],
    [
        (PF_IMAGE,      'image',    'Opened image', None) 
    ],
    make_trees,
    menu='<Image>/File/Open'
)


main()

