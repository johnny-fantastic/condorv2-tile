import sys,os,os.path,re,glob,traceback
from gimpfu import *


#sys.stderr = open( 'c:\\temp\\gimpstderr.txt', 'w')
#sys.stdout = open( 'c:\\temp\\gimpstdout.txt', 'w')
    
def iterate_tiles(terragen_col, terragen_row):
    column_base = terragen_col * 4
    row_base = terragen_row *4
    for column in range(4):
        for row in range(4):
            yield column+column_base, row+row_base,3-column,3-row


def convert_files(directory, namePattern):
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
            image.undo_thaw()
            pdb.gimp_image_delete(image)

    except Exception as e:
        pdb.gimp_message(e.args[0])
        print traceback.format_exc()

    print 'split complete!'

author='bluefang'
year='2020'
exportMenu='<Image>/File/Export/Export Condor Tiles'
exportDesc='Split image into 4x4 grid and export each to condor formatted tCCRR.dds file'
openDesc='Split files into 4x4 grid and export each grid to condor formatted .dds file'
whoiam='\n'+os.path.abspath(sys.argv[0])

register(
    'split-to-condor-tiles',
    openDesc,openDesc+whoiam,author,author,year,'Split to Condor files...',
    '',
    [
        (PF_DIRNAME,    'directory',    'Directory',   '.'),
        (PF_STRING,     'namePattern',  'Tile name',   '*.png')
    ],
    [
        (PF_IMAGE,      'image',    'Opened image', None) 
    ],
    convert_files,
    menu='<Image>/File/Open'
)

main()


