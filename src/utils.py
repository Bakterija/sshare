from hashlib import sha512
import random
import string
import os

SIMPLE_CHARS = string.ascii_letters + string.digits

def dround(number):
    return round(number, 2)

def get_files(path, filter_ext=None):
    '''Finds and returns list of all files in path and sub directories in it'''
    templist = []
    for dirname, dirnames, filenames in os.walk(path):
        for file_name in filenames:
            file_path = os.path.join(dirname, file_name)
            if filter_ext:
                can_add = False
                for ext in filter_ext:
                    len_ext = len(ext)
                    if file_path[-len_ext:] == ext:
                        can_add = True
                    if can_add:
                        templist.append(file_path)
                        break
            else:
                templist.append(file_path)
    return templist

def get_dirs(path):
    '''Finds and returns list of all files in path and sub directories in it'''
    templist = []
    for dirname, dirnames, filenames in os.walk(path):
        for dir_name in dirnames:
            templist.append((
                '%s/%s'% (path, dir_name),
                dir_name))
    return templist

def get_random_string(length):
    random_string = ''.join(random.choice(SIMPLE_CHARS) for i in range(length))
    hsh = sha512()
    hsh.update(random_string.encode('utf-8'))
    return hsh.hexdigest()[:length]
