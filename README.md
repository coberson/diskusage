# diskusage
Chantal Oberson Ausoni, 15/11/2016

Python mini project suggested on the FUN Python MOOC

***script to show disk usage and clean directories on your disk***

During a first scan (pass1), all directories are scanned, the sizes of directories are computed and stored in a cache and in .du files situated in the directories.
During the pass2, the user can scan directories and interact (move to a directory, list files, delete file or directory, toggle verbose on/off). 

usage: python diskusage.py [-h] [-1] [-b] [-v] dir_to_check

show disk usage and clean directories

positional arguments:
  dir_to_check

optional arguments:
  -h, --help         show this help message and exit
  -1, --pass1        Run pass1, that computes .du in all subdirs
  -b, --both_passes  Run pass1, that computes .du in all subdirs,and then
                     pass2 that is interactive
  -v, --verbose      increase output verbosity


works with python 2.7, will be adapted soon for python 3.5
