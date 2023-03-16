#!/usr/bin/python
from pysh import Pysh
source_file = __file__
pysher = Pysh(source_file)
#$ echo "pysh enabled"



blocks = pysher.findblocks()
blocks[0].runp() # Will print stdout with label for block

# Switch to another source file - can then run another pysh interpeter
# pysher.updatesrc(__file__)

# Get information about the script blocks at runtime
t_block = pysher.blocks[0]
print(t_block.hasrun, t_block.returncode)

pysher.shyp()