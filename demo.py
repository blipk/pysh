#!/usr/bin/python

from pysh import pysh, Pysh

p = Pysh(__file__)

#$ echo "Pysh activated"

from pprint import pprint
blocks = p.findblocks()
pprint(blocks)

[block.runp() for block in blocks]

#$ ls . # comment
##$ xdg-open . # double comment to disable in pysh


src = ""#$ echo "multiline"
#$ echo "l1"
#$ echo "l2"
#$ echo "l3"

##$ firefox https://news.ycombinator.com && echo "opened link in firefox"