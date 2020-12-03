# RGB-Astronomy-Image-Generator
This code is designed to take a file directory with multiple RGB FITS images in three individual bands and output false-color images

Code will also **rename files** based on target and band and will output a summary file with info about the new file name and target data

Optional to view and save histograms of selected object and band

Ensure that all files are in .fts or .fits format (.fits files will be converted)

If required info is not in header, program will ask the user to manually determine and enter and will rewrite header info with inputs

Some FITS images may have issues with sizing and values, this is a limited case-by-case basis so there's no solution other than user manipulation of the code
