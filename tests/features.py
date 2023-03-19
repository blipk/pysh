#!/usr/bin/python
import os
print("####BEGIN TEST", os.environ.get("PYSH_ROOT", None), os.environ.get("PYSH_RUNNING", None), os.environ.get("PYSH_BLOCK", None))

from pysh import Pysh
source_file = __file__
pysher = Pysh(source_file, test_mode=False)
pysher.shyp()

# Alternate shells
text = "The time and date"
import time
ttime = time.asctime()
py_stdout = ""#$!python import time; print("{$text$}", "{$ttime$}")
print("py_stdout = ", py_stdout)
should_be = bytes((text + " " + ttime + "\n").encode("UTF-8"))
assert py_stdout == should_be, f"py_stdout is wrong: {py_stdout}"

# print(pysher.blocks[0])

# Current directory
stdout = ""#$ echo "$PWD"
assert stdout.decode("UTF-8").strip() == os.getcwd(), f"$PWD from script is wrong {stdout}"
print("CWD:", stdout)

# External scripts
#$ chmod +x tests/myscript.sh
extern_stdout = ""#$$ tests/myscript.sh "argone" "argtwo"
assert extern_stdout == b"external script. args: argone argtwo\n", "external script output is wrong"
print("Extern:", extern_stdout)


print("Test Passed")
