#!/usr/bin/env python3
import sys
import os

npath = os.path.abspath(os.path.dirname(__file__)) + '/src/'
os.chdir(npath)
sys.path.append(npath)
import main

if __name__ == '__main__':
    main.start()
