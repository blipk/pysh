#!/usr/bin/python
import os
print("####BEGIN TEST", os.environ.get("PYSH_ROOT", None), os.environ.get("PYSH_RUNNING", None), os.environ.get("PYSH_BLOCK", None))
from pysh import Pysh
source_file = __file__
pysher = Pysh(source_file)
pysher.shyp()

stdout = ""#$@ echo "pysh activated"
assert stdout == b"pysh activated\n", f"stdout wrong: {stdout}"

print("WAIT for user dialog")
#$ /usr/bin/zenity --info # pause here

print("STDOUT BLOCKED IN BETWEEN BLOCKS")

text = "pysh test"
multiline_stdout = ""#$ echo "{$text$}"
#$ echo "pysh test line 2"
assert multiline_stdout == b"pysh test\npysh test line 2\n", f"multiline_stdout wrong: {multiline_stdout}"

more_lines_stdout = ""#$ echo "one"
#$ echo "two"
#$ echo "three"

assert more_lines_stdout == b"""one
two
three
""", f"more lines failure {more_lines_stdout}"

print("Test Passed")