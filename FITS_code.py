#This code is designed to take a file directory with multiple RGB FITS images in three individual bands and output false-color images
#Code will also rename files based on target and band and will output a summary file with info about the new file name and target data
#Optional to view and save histograms of selected object and band
#Ensure that all files are in .fts format
#If required info is not in header, program will ask the user to manually determine and enter
#Some FITS images may have issues with sizing and values, this is a limited case-by-case basis so there's no solution other than user manipulation of the code

import glob
import os
import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image
from astropy.io import fits
from matplotlib.colors import LogNorm

#Gets all files from directory
while True:
    dir_input = input('Input directory with FITS files: ') #Asks for inputted directory
    if not os.path.exists(os.path.dirname(dir_input)): #Checks if directory is valid
        print('Not a valid directory')
        continue
    else:
        break

fits_glob = sorted(glob.glob(dir_input + '/*.fits')) #Finds ant .fits images and converts them to .fts
for file in fits_glob:
    my_file = file
    base = os.path.splitext(my_file)[0]
    os.rename(my_file, base + '.fts')

files = sorted(glob.glob(dir_input + '/*.fts')) #Creates sorted glob for all .fts files in directory
sum_fhand = open(dir_input + '/summary.txt', 'w') #Creates summary text file

band_list = []
obj_list = []
#Renames the files based on object and band along with creating summary
for file in files:
    fits_image_filename = file
    hdul = fits.open(fits_image_filename)
    hdr = hdul[0].header #Defines Header
    data, header = fits.getdata(file, header=True) #Lots data and header for rewrite
    file_name = fits_image_filename.replace(dir_input + '/', '') #Gets only the file name by removing directory from string
    #Checks if necessary keywords in FITS header
    tar_check = 'OBJECT' in hdr
    band_check = 'FILTER' in hdr
    obsinfo_check = 'OBSERVER' in hdr
    bands = ['Red','Green','Blue'] #Acceptably defined bands
    if tar_check == True and band_check == True:
        tar = hdr['OBJECT'] #Finds target from header
        band = hdr['FILTER'] #Finds band from header
    else: #If object and filter aren't defined, user inputs manually
        print('\n'+file)
        tar = input('Manually determine target and input: ')
        header['OBJECT'] = tar #Rewrites header data for defined target
        while True:
            band = input('Manually determine band and input as Red, Green, or Blue: ')
            if band in bands:
                header['FILTER'] = band #Rewrites header data for defined band
                break
            else:
                print('Not valid band')
                continue
    test = band in bands
    if test == False: #If filter is defined but not as 'Red', 'Green', or 'Blue', user must input manually
        print('\n'+file)
        print('{} not recognized as Red, Green, or Blue'.format(band))
        while True:
            band = input('Determine and enter as such: ')
            if band in bands:
                header['FILTER'] = band #Rewrites header data for defined band
                break
            else:
                print('Not valid band')
                continue
    if obsinfo_check == True:
        obs = hdr['OBSERVER'] #Finds observatory from header
        inst = hdr['INSTRUME'] #Finds instrument from header
        tele = hdr['TELESCOP'] #Finds telescope from header
        date = hdr['DATE'] #Finds date of observation from header
        msg2 ='Said target was observed by the {} on the {} at {} on {}.'.format(inst,tele,obs,date)
    msg1 = '{}: Target is {} in {} band'.format(file_name,tar,band)
    new_name = '{}_{}.fts'.format(tar,band) #Renames file to "target"_"band".fts
    new_dir = '{}/{}'.format(dir_input,new_name) #Creates new directory with new file name
    msg3 = 'File {} is now under {}'.format(fits_image_filename,new_dir)
    os.rename(file, new_dir) #Renames file with new directory and name
    if 'msg2' in globals():
        sum_fhand.write(msg1 + '\n' + msg2 + '\n' + msg3 + '\n\n') #Adds summary to text file for all files w/ observing info
    else:
        sum_fhand.write(msg1 + '\n' + msg3 + '\n\n') #Adds summary to text file for all files w/o observing info
    fits.writeto(new_dir, data, header, overwrite=True)
    band_list.append(band) #Adds band to list
    obj_list.append(tar) #Adds target to list
sum_fhand.close()

#Takes all duplicate bands and removes them, leaving list with unique bands
bands = []
for i in band_list: 
    if i not in bands: 
        bands.append(i)

#Takes all duplicate targets and removes them, leaving list with unique targets
objs = [] 
for i in obj_list: 
    if i not in objs: 
        objs.append(i)

#If you want to view histogram of image data:
hist_inp = input('\n'+'Do you want to view a histogram of the data for your frame? (yes/no): ')
hist_answer = hist_inp.upper()

#Plots Histogram
if not os.path.exists(dir_input + '/Histograms'): #Creates new folder for historgrams if it doesn't already exist
    os.makedirs(dir_input + '/Histograms')
while True:
    if hist_answer == 'YES':
        print('Which target?', objs) #Requests object from list
        chosen_obj = input()
        print('Which band?', bands) #Requests band from list
        chosen_band = input()
        if chosen_band not in bands or chosen_obj not in objs: #Checks if the band and object are not valid
            print('One of the inputs not in list, try again')
            continue
        chosen_file = '{}_{}.fts'.format(chosen_obj,chosen_band)
        image_file = dir_input + '/' + chosen_file
        #Extracts image data and plots in y-scale log histgram
        hdu_list = fits.open(image_file)
        hist_data = hdu_list[0].data
        hist_data = hist_data.astype('uint16') #Converts all data input into uint16 format
        peak = np.bincount(hist_data.flatten()).argmax()
        hdu_list.close()
        histogram = plt.hist(hist_data.flatten(), 1000, color = 'k')
        plt.title('{}, {} Band'.format(chosen_obj,chosen_band))
        plt.yscale('log')
        plt.savefig(dir_input + '/Histograms/{}_{}_Hist.png'.format(chosen_obj, chosen_band)) #Saves figure to histogram folder
        plt.show()
        break
    else:
        break

objs.append('ALL')
#Input for which target the user wants to use to create the RGB image
while True:
    print('\n'+'Which target for RGB image?', objs)
    print('Input "ALL" for non-adjustable images of all objects')
    chosen_obj = input()
    if chosen_obj not in objs:
        print('Input not in list, try again')
        continue
    break
objs.remove('ALL')

total = len(objs)
complete = 1
#Creats quick images for all objects in directory without option for image adjustment
if chosen_obj == 'ALL':
    for objects in objs:
        red_file = '{}_Red.fts'.format(objects)
        image_file = dir_input + '/' + red_file
        hdu_list = fits.open(image_file)
        image_data = hdu_list[0].data
        if image_data.dtype != 'uint16': #if not in the required format, must be converted and plotted differently
            red_file = '{}_Red.fts'.format(objects)
            image_file = dir_input + '/' + red_file
            hdu_list = fits.open(image_file)
            image_data = hdu_list[0].data
            image_data = image_data.astype('uint16') #Converst nparray to uint16 format
            image_data[0,0] = 0
            LOGMIN = .3 #Arbitrary value
            plt.imshow(image_data, cmap='gray', norm=LogNorm(), vmin = max(image_data.min(), LOGMIN))
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/redband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300) #Saves plot for stacking

            green_file = '{}_Green.fts'.format(objects)
            image_file = dir_input + '/' + green_file
            hdu_list = fits.open(image_file)
            image_data = hdu_list[0].data
            image_data = image_data.astype('uint16')
            image_data[0,0] = 0
            LOGMIN = 30
            plt.imshow(image_data, cmap='gray', norm=LogNorm(), vmin = max(image_data.min(), LOGMIN))
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/greenband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300)

            blue_file = '{}_Blue.fts'.format(objects)
            image_file = dir_input + '/' + blue_file
            hdu_list = fits.open(image_file)
            image_data = hdu_list[0].data
            image_data = image_data.astype('uint16')
            image_data[0,0] = 0
            LOGMIN = .3
            plt.imshow(image_data, cmap='gray', norm=LogNorm(), vmin = max(image_data.min(), LOGMIN))
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/blueband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300)
        else:
            #Red
            rmargin1 = 15 #Default min parameter
            rmargin2 = 175 #Default max parameter
            red_file = '{}_Red.fts'.format(objects)
            image_file = dir_input + '/' + red_file
            #Gets image data for red band from inputted target
            hdu_list = fits.open(image_file)
            image_data = hdu_list[0].data
            hdu_list.close()
            peak = np.bincount(image_data.flatten()).argmax() #Finds the value with the highest frequency
            min_param = peak-rmargin1 #Sets min parameter to a certain margin below peak (default 25)
            max_param = peak+rmargin2 #Sets max parameter to a certain margin above peak (default 125)
            plt.imshow(image_data, cmap='gray', norm=LogNorm(min_param, max_param)) #Plots red band with red colormap
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/redband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300) #Saves plot for stacking

            #Green
            #Green min and max carry over red min and max values over to remain consistent with any user tweaks
            gmargin1 = rmargin1
            gmargin2 = rmargin2
            green_file = '{}_Green.fts'.format(objects)
            image_file2 = dir_input + '/' + green_file
            hdu_list2 = fits.open(image_file2)
            image_data2 = hdu_list2[0].data
            hdu_list2.close()
            peak2 = np.bincount(image_data2.flatten()).argmax()
            min_param2 = peak2-gmargin1
            max_param2 = peak2+gmargin2
            plt.imshow(image_data2, cmap='gray', norm=LogNorm(min_param2, max_param2))
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/greenband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300)

            #Blue
            bmargin1 = rmargin1
            bmargin2 = rmargin2
            blue_file = '{}_Blue.fts'.format(objects)
            image_file3 = dir_input + '/' + blue_file
            hdu_list3 = fits.open(image_file3)
            image_data3 = hdu_list3[0].data
            hdu_list3.close()
            peak3 = np.bincount(image_data3.flatten()).argmax()
            min_param3 = peak3-bmargin1
            max_param3 = peak3+bmargin2
            plt.imshow(image_data3, cmap='gray', norm=LogNorm(min_param3, max_param3))
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/blueband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300)
        
        #Stack 
        img1 = Image.open(dir_input+'/redband.png')
        img2 = Image.open(dir_input+'/greenband.png')
        img3 = Image.open(dir_input+'/blueband.png')
        data = np.array(img1, dtype='uint8')
        data2 = np.array(img2, dtype='uint8')
        data3 = np.array(img3, dtype='uint8')
        #Converts images to single channel
        data = data[:,:,0]
        data2 = data2[:,:,0]
        data3 = data3[:,:,0]

        rgb = np.dstack((data,data2,data3)) #Stack the three arrays
        plt.imshow(rgb, cmap = 'hsv') #Shows stacked image and applies HSV colormap
        #Removes white space and axes
        final_file = 'RawFinal_{}'.format(objects)
        plt.title(objects)
        plt.gca().set_axis_off()
        plt.savefig(dir_input+'/'+final_file, bbox_inches = 'tight', dpi=300) #Saves final image in inputted directory
        plt.close()

        #Removes temporary band files used for stacking
        os.remove(dir_input+'/redband.png')
        os.remove(dir_input+'/greenband.png')
        os.remove(dir_input+'/blueband.png')

        print('{} out of {} images finished'.format(complete,total)) #Counter for progress
        complete+=1

#Individual object image with band-by-band adjustment
else:
    red_file = '{}_Red.fts'.format(chosen_obj)
    image_file = dir_input + '/' + red_file
    hdu_list = fits.open(image_file)
    image_data = hdu_list[0].data
    if image_data.dtype != 'uint16': #For certain FITS files not originally compatible with Astropy
        LOGMIN1 = .8
        LOGMIN2 = 30
        LOGMIN3 = .1
        while True:
            red_file = '{}_Red.fts'.format(chosen_obj)
            image_file = dir_input + '/' + red_file
            hdu_list = fits.open(image_file)
            image_data = hdu_list[0].data
            image_data = image_data.astype('uint16')
            image_data[0,0] = 0 #Removes negative values
            plt.imshow(image_data, cmap='gray', norm=LogNorm(), vmin = max(image_data.min(), LOGMIN1))
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/redband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300) #Saves plot for stacking
            plt.show()
            question = input('\n'+'Is the contrast correct?: ')
            response = question.upper()
            if response == 'NO':
                second_question = input('Too much or too little?: ')
                response2 = second_question.upper()
                if response2 == 'TOO LITTLE':
                    LOGMIN1+=20
                if response2 == 'TOO MUCH':
                    if LOGMIN1 < .3:
                        print('Cannot minimize further')
                    else:
                        LOGMIN1-=.2
                continue
            else:
                break
        while True:
            green_file = '{}_Green.fts'.format(chosen_obj)
            image_file = dir_input + '/' + green_file
            hdu_list = fits.open(image_file)
            image_data = hdu_list[0].data
            image_data = image_data.astype('uint16')
            image_data[0,0] = 0
            plt.imshow(image_data, cmap='gray', norm=LogNorm(), vmin = max(image_data.min(), LOGMIN2))
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/greenband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300)
            plt.show()
            question = input('\n'+'Is the contrast correct?: ')
            response = question.upper()
            if response == 'NO':
                second_question = input('Too much or too little?: ')
                response2 = second_question.upper()
                if response2 == 'TOO LITTLE':
                    LOGMIN2+=20
                if response2 == 'TOO MUCH':
                    if LOGMIN2 < .3:
                        print('Cannot minimize further')
                    else:
                        LOGMIN2-=.2
                continue
            else:
                break
        while True:
            blue_file = '{}_Blue.fts'.format(chosen_obj)
            image_file = dir_input + '/' + blue_file
            hdu_list = fits.open(image_file)
            image_data = hdu_list[0].data
            image_data = image_data.astype('uint16')
            image_data[0,0] = 0
            plt.imshow(image_data, cmap='gray', norm=LogNorm(), vmin = max(image_data.min(), LOGMIN3))
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/blueband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300)
            plt.show()
            question = input('\n'+'Is the contrast correct?: ')
            response = question.upper()
            if response == 'NO':
                second_question = input('Too much or too little?: ')
                response2 = second_question.upper()
                if response2 == 'TOO LITTLE':
                    LOGMIN3+=20
                if response2 == 'TOO MUCH':
                    if LOGMIN3 < .3:
                        print('Cannot minimize further')
                    else:
                        LOGMIN3-=.2
                continue
            else:
                break
    else:
        #Red
        rmargin1 = 15 #Default min parameter
        rmargin2 = 175 #Default max parameter
        while True:
            red_file = '{}_Red.fts'.format(chosen_obj)
            image_file = dir_input + '/' + red_file
            #Gets image data for red band from inputted target
            hdu_list = fits.open(image_file)
            image_data = hdu_list[0].data
            hdu_list.close()
            peak = np.bincount(image_data.flatten()).argmax() #Finds the value with the highest frequency
            min_param = peak-rmargin1 #Sets min parameter to a certain margin below peak (default 25)
            max_param = peak+rmargin2 #Sets max parameter to a certain margin above peak (default 125)
            plt.imshow(image_data, cmap='gray', norm=LogNorm(min_param, max_param)) #Plots red band with red colormap
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/redband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300) #Saves plot for stacking
            plt.show()
            question = input('\n'+'Is the contrast correct?: ') #Allows for manual image adjustment
            response = question.upper()
            if response == 'NO':
                second_question = input('Too much or too little?: ')
                response2 = second_question.upper()
                if response2 == 'TOO LITTLE': #Widens margin
                    rmargin1 -=10
                    rmargin2 +=50
                if response2 == 'TOO MUCH': #Narrows margin
                    rmargin1 +=10
                    rmargin2 -=50
                continue
            else:
                break

        #Green
        #Green min and max carry over red min and max values over to remain consistent with any user tweaks
        gmargin1 = rmargin1
        gmargin2 = rmargin2
        while True:
            green_file = '{}_Green.fts'.format(chosen_obj)
            image_file2 = dir_input + '/' + green_file
            hdu_list2 = fits.open(image_file2)
            image_data2 = hdu_list2[0].data
            hdu_list2.close()
            peak2 = np.bincount(image_data2.flatten()).argmax()
            min_param2 = peak2-gmargin1
            max_param2 = peak2+gmargin2
            plt.imshow(image_data2, cmap='gray', norm=LogNorm(min_param2, max_param2))
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/greenband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300)
            plt.show()
            question = input('\n'+'Is the contrast correct?: ')
            response = question.upper()
            if response == 'NO':
                second_question = input('Too much or too little?: ')
                response2 = second_question.upper()
                if response2 == 'TOO LITTLE':
                    gmargin1 -=10
                    gmargin2 +=50
                if response2 == 'TOO MUCH':
                    gmargin1 +=10
                    gmargin2 -=50
                continue
            else:
                break

        #Blue
        bmargin1 = rmargin1
        bmargin2 = rmargin2
        while True:
            blue_file = '{}_Blue.fts'.format(chosen_obj)
            image_file3 = dir_input + '/' + blue_file
            hdu_list3 = fits.open(image_file3)
            image_data3 = hdu_list3[0].data
            hdu_list3.close()
            peak3 = np.bincount(image_data3.flatten()).argmax()
            min_param3 = peak3-bmargin1
            max_param3 = peak3+bmargin2
            plt.imshow(image_data3, cmap='gray', norm=LogNorm(min_param3, max_param3))
            plt.gca().set_axis_off()
            plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
            plt.margins(0,0)
            plt.gca().xaxis.set_major_locator(plt.NullLocator())
            plt.gca().yaxis.set_major_locator(plt.NullLocator())
            plt.savefig(dir_input + '/blueband.png', bbox_inches = 'tight', pad_inches = 0, dpi=300)
            plt.show()
            question = input('\n'+'Is the contrast correct?: ')
            response = question.upper()
            if response == 'NO':
                second_question = input('Too much or too little?: ')
                response2 = second_question.upper()
                if response2 == 'TOO LITTLE':
                    bmargin1 -=10
                    bmargin2 +=50
                if response2 == 'TOO MUCH':
                    bmargin1 +=10
                    bmargin2 -=50
                continue
            else:
                break

    #Stack 
    img1 = Image.open(dir_input+'/redband.png')
    img2 = Image.open(dir_input+'/greenband.png')
    img3 = Image.open(dir_input+'/blueband.png')
    data = np.array(img1, dtype='uint8')
    data2 = np.array(img2, dtype='uint8')
    data3 = np.array(img3, dtype='uint8')
    #Converts images to single channel
    data = data[:,:,0]
    data2 = data2[:,:,0]
    data3 = data3[:,:,0]

    rgb = np.dstack((data,data2,data3)) #Stack the three arrays
    plt.imshow(rgb, cmap = 'hsv') #Shows stacked image and applies HSV colormap
    #Removes white space and axes
    final_file = 'Final_{}'.format(chosen_obj)
    plt.title(chosen_obj)
    plt.gca().set_axis_off()
    plt.savefig(dir_input+'/'+final_file, bbox_inches = 'tight', dpi=300) #Saves final image in inputted directory
    plt.show()

    #Removes temporary band files used for stacking
    os.remove(dir_input+'/redband.png')
    os.remove(dir_input+'/greenband.png')
    os.remove(dir_input+'/blueband.png')
    
print('Done!')