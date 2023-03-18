#!/usr/bin/python
print("####BEGIN SOURCE")
from pprint import pprint

from pysh import Pysh
source_file = __file__
pysher = Pysh(source_file)

blocks = pysher.findblocks()
# print(len(blocks))
# pprint(blocks)
# blocks[0].runp() # Will print stdout with label for block
# t_block = pysher.blocks[0]
# print(t_block.hasrun, t_block.returncode)



# Switch to another source file - can then run another pysh interpeter
# pysher.updatesrc(__file__)

pysher.shyp()
print("####BEGIN PYSH")
#$ echo "pysh enabled"

print("IN BETWEEN BLOCKS")

test = ""#$ echo "pysh test"
#$ echo "pysh test line 2"

print("TEST RESULT", test)

print("Complete")
