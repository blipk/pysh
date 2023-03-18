#!/usr/bin/python
import os
print("####BEGIN SOURCE", os.environ.get("PYSH_ROOT", None), os.environ.get("PYSH_RUNNING", None), os.environ.get("PYSH_BLOCK", None))
from pprint import pprint

from pysh import Pysh
source_file = __file__
pysher = Pysh(source_file)
pysher.shyp()

print("####BEGIN PYSH")
#$ echo "pysh enabled"

print("IN BETWEEN BLOCKS")

test = ""#$ echo "pysh test"
#$ echo "pysh test line 2"

print("TEST RESULT", test)

print("Complete")
