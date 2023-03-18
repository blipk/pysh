#!/usr/bin/python
print("####BEGIN SOURCE")
from pprint import pprint

from pysh import Pysh
source_file = __file__
pysher = Pysh(source_file)

blocks = pysher.findblocks()
pysher.shyp()

print("####BEGIN PYSH")
#$ echo "pysh enabled"

print("IN BETWEEN BLOCKS")

test = ""#$ echo "pysh test"
#$ echo "pysh test line 2"

print("TEST RESULT", test)

print("Complete")
