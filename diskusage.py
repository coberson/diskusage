from __future__ import print_function
from builtins import input
import argparse
import os
import os.path
import operator
import shutil


help_pass2 = """num  go to listed directory number 'num'
cnum list files and directories in directory number 'num'(for example: c11)
c    clean current directory
+    (default) go to last (and thus biggest) directory
u    go one step up - can be also '0' or '..'
l    list files in the current directory
.    come again (stay in place)
!    re-run pass1
v    toggle verbose on and off
q    quit
h    this help"""


class HumanReadableSize(int):
    """display sizes in a readable format (139.73 KiB or 1.09 MiB)"""
    def __init__(self, val):
        self.val = val
    
    def __repr__(self):
        return fmt(self.val)
    
    def __str__(self):
        return fmt(self.val)
    
def fmt(num):
    """convert size int into readable string (Bytes)"""
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return '{0:7.2f} {1}B'.format(num, unit)
        num /= 1024.0
    return '{0:.2f}YiB'.format(num)
    
class Cache(dict):
    """dictionnary to store total size of directories in memory"""
    def __init__(self):
        dict.__init__(self)
    def __getitem__(self, path):
        """look first in cache, the in .du file, else return 0"""
        du_file = path + "/.du"
        if path in self.keys():
            return dict.__getitem__(self, path)
        elif os.path.exists(du_file):
            with open(du_file,"r") as f:
                size = HumanReadableSize(int(f.readline()))
                dict.__setitem__(self,path,size)
                return size
        else:
            return HumanReadableSize(0)
    def __setitem__(self, path, size):
        """write the size in cache,
        try and write the size in a .du file, OK if not working"""
        du_file = path + "/.du"
        dict.__setitem__(self,path,size)
        if os.path.isdir(path):
            with open(du_file,"w") as f:
                f.write(str(size.val))
    def __repr__(self):
        """output of the cache in a string, for debugging purposes"""
        sorted_list = sorted(self.items(), key=operator.itemgetter(1))
        dir_name = os.path.dirname(sorted_list[0][0])
        total_size = HumanReadableSize(sum([x.val for x in self.values()]))
        descr = "-------- Path {} has a total size of {}\n".format(dir_name, total_size)
        count = 0
        for couple in sorted_list:
            file_name = couple[0]
            file_size = couple[1]
            count += 1
            descr += "{}\t{}\t{}\n".format(count,file_size,file_name)
        descr += "Enter number (h for help)\n"
        return descr
    
class TopLevelDir(object):
    """input dir with cache dictionnary"""
    def __init__(self, dir_to_check):
        self.dir_to_check = dir_to_check
        self.cache = Cache()
        
    def pass1(self, verbose):
        """scan a whole tree, and write directory sizes in .du files;
        write a Cache object so that pass2 does not read .du files"""
        
        for root, dirs, files in os.walk(self.dir_to_check, topdown=False):
            t_size = 0
            for f in files:
                new_f = os.path.join(root,f) #complete path in case of homonyms
                size = os.path.getsize(new_f)
                t_size += size
                self.cache[new_f] = HumanReadableSize(size)
            t_size += sum ([self.cache[os.path.join(root,d)].val for d in dirs])
            self.cache[root] = HumanReadableSize(t_size)
            if verbose:
                print ('.................... Computing size of {}!'.format(root))
            
        #print (self.cache) #debugging
    
    def pass2(self):
        """entry point for pass2:
        display the directories and enable actions (move, ...)
        as long as no 'q'-input"""
        current_dir = self.dir_to_check
        car = 'e'
        while current_dir != None:
            subdirs = self.print_current_dir(current_dir)
            if subdirs == []: 
                current_dir = self.move_to_parent(current_dir)
                print\
                  ('\n=> Choose options for parent directory {}!'.format(current_dir))
                subdirs = self.print_current_dir(current_dir)
            car = input("Enter number (h for help)\n")
            current_dir = self.act_after_input(current_dir, subdirs, car)
            
    def move_to_parent(self, path):
        """move to path directory"""
        if path == self.dir_to_check:
            print ('      Parent directory out of scope!')
            return path
        else:
            dir_name = os.path.dirname(path)
            return dir_name

    def list_files(self, path):
        """display list of plain files in a given dir
        sorted largest last"""
        print ('\t\t********************************************')
        print ('\t\t* list of files in ',path)
        dirs_and_files = (os.path.join(path, d) for d in os.listdir(path))
        files = [f for f in dirs_and_files if os.path.isfile(f) and not    os.path.basename(f).startswith('.')]
        files.sort(key = lambda f: os.path.getsize(f))
        count = 0
        if files:
            for f in files:
                count += 1
                new_f = os.path.basename(f)
                print ("\t\t*F\t{}\t{}\t{}".format(count, new_f, self.cache[new_f]))
        else:
            print ('\t\t No files in ' + path)
        print ('\t\t********************************************')
                
    def act_after_input(self, current_dir, subdirs, car):
        """according to input character,
        move to directory, list files, quit, toggle verbose on/off ... """
        new_dir = current_dir
        if car == 'q':
            new_dir = None
        elif car in {str(i+1) for i in range(len(subdirs))}:
            print ('----> Moving to directory', subdirs[int(car)-1])
            new_dir = subdirs[int(car)-1]
        elif car=='.':
            pass
        elif car == 'l':
            self.list_files(current_dir)
        elif car == '!':
            self.pass1(self.verb)
        elif car in {'u','0','..'}:
            print ('----> Moving one step up')
            new_dir = self.move_to_parent(current_dir)
        elif car == '+':
            new_dir = subdirs[len(subdirs)-1]
        elif car == 'v':
            self.verb = not self.verb
        elif car[0] == 'c': 
            if len(car)>1:
                num = car[1:]
                if num in {str(i+1) for i in range(len(subdirs))}:
                    self.list_for_clean(subdirs[int(num)-1])
            else:
                self.list_for_clean(current_dir)
        else:
            print (help_pass2)
        return new_dir

    def print_current_dir(self, path):
        """display the sorted list of directories in the path directory"""
        dirs_and_files = (os.path.join(path, d) for d in os.listdir(path))
        dirs = [d for d in dirs_and_files  if os.path.isdir(d)]
        dirs.sort(key = lambda d: self.cache[d])
        print ("-------- Path {} has a total size of{}".\
                                format(path, self.cache[path]))
        count = 0
        if dirs:
            for d in dirs:
                count += 1
                print ("{}\t{}\t{}".format(count,os.path.basename(d),self.cache[d]))
        else:
            print ('\tNo subdirectories in ' + path)
            self.list_files(path)
        return dirs

    def list_for_clean(self,path):
        """display the sorted list of directories and files in the path directory;
        for input nu, delete file or directory number 'nu' """
        nu = -1
        
        dirs_and_files = [os.path.join(path, d) for d in os.listdir(path) if not  os.path.basename(d).startswith('.')]
        dirs_and_files.sort(key = lambda d: self.cache[d])
        while nu != 0:
            if nu>0:
                d = dirs_and_files[nu-1]
                rep = 'o'
                while rep not in ['y','n']:
                    rep = input("Do you want to delete {}? y/n\n".format(d))
                if rep == 'y':
                    #dd = os.path.join(path,d)
                    if os.path.isfile(d):
                        os.remove(d)
                        del self.cache[d]
                    else:
                        shutil.rmtree(d)
                        del self.cache[d]
                dirs_and_files = [os.path.join(path, d) for d in os.listdir(path)
                                 if not  os.path.basename(d).startswith('.')]
                dirs_and_files.sort(key = lambda d: self.cache[d])
                t_size = sum ([self.cache[d].val for d in dirs_and_files])
                self.cache[path] = HumanReadableSize(t_size)
            
            print ("\t\t-------------Cleaning {} - total size of{}".\
                                format(path, self.cache[path]))
            count = 0
            if not dirs_and_files:
                print ("\t\t|Empty directory!!!!!!!!!!")
                break
            else:
                for d in dirs_and_files:
                    count += 1
                    if os.path.isfile(d):
                        print ("\t\t|F\t{}\t{}\t{}".\
                            format(count,os.path.basename(d), self.cache[d]))
                    else:
                        print ("\t\t|D\t{}\t{}\t{}".\
                            format(count,os.path.basename(d),self.cache[d]))
                rep = -1
                while rep not in {str(i) for i in range(count+1)}:
                    rep = input("Enter number to delete file or dir, 0 to quit cleaning\n")
                nu = int(rep)
            
                    
def main():
    """parse the command line arguments
    using an instance of ArgumentParser;
    create an instance of ToplevelDir
    and send it the pass1() and/or pass2() methods;
    return an int 0 when everything is fine and 1 otherwise
    """
    parser = argparse.ArgumentParser(description='show disk usage and clean directories')
    
    parser.add_argument("dir_to_check")
    parser.add_argument("-1","--pass1", action="store_true", \
                        help="Run pass1, that computes .du in all subdirs")
    parser.add_argument("-b", "--both_passes", action="store_true",\
                        help="Run pass1, that computes .du in all subdirs,and then pass2 that is interactive")
    parser.add_argument("-v", "--verbose", action="store_true",\
                        help="increase output verbosity")
    args = parser.parse_args()
    
    my_dir = TopLevelDir(args.dir_to_check)
    
    my_dir.verb = False
    if args.verbose:
        my_dir.verb = True
    if args.pass1:
        my_dir.pass1(my_dir.verb)
    if args.both_passes:
        my_dir.pass1(my_dir.verb)
        my_dir.pass2()
        

    
if __name__ == '__main__':
    main()