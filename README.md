## Pysh/Pype

Python source file preprocessor/interpreter and subprocess pipe manager to enable running in-line bash/shell code during python runtime.

```Python
#!/usr/bin/env python
from pysh import pysh
pysh()

#$@ echo "Pysh activated"
stdout = ""#$ echo "This is standard out"
print(stdout)

##@!python print("Python through a pysh pype")
```

Use #$ flagged directives to signify shell code to be piped through a subprocess.

##### Real usage
```Python
# Script your system in parallel with your python code execution
# Do anything you can in bash e.g.

build_service()
#$ cd ~/hosted/myservice && docker compose up

aggregate_assets()
crf = "23"
in_file = "/path/in.mp4"
out_file = "/path/out.mp4"
fmpg_result = ""#$ ffmpeg -i {$in_file$} \
#$ -crf {$crf$} -o {$out_file$} \
#$ && rm {$in_file$}
process_assets(process_fmpg_stdout(fmpg_result))

print("Process complete")
```

### Installation
From PyPI:

`pip3 install pyshpype`

Git to local folder:

`pip3 install -e "git+https://github.com/blipk/pysh.git#egg=pysh"`



###### General syntax
```Python
#!/usr/bin/python
# This is a python comment
#$  ls .         # pysh eol comment
##$ sudo rm -rf  # disable pysh line with pysh comment

# Pass any python variable thats in scope to the pysh script
my_var = "hello"
stdout = ""#$ echo "{$myvar$}"

# run external script with double $
#$$ my_script.sh

# optionally pass arguments to it
#$$ argumentative_script.sh arg1 arg2

# Use the ! flag to change the shell that interprets the script
# must support -c command_strings or filepath if external $$
#$!sh echo "simple"
#$!perl oysters.pl
#$$@!bash printscript.sh

# Multiple flags/features
stdout = ""#$@!python import time
#$ print("The time and date", time.asctime())

# Use the % flag to catch errors,
# otherwise they will be printed but not raised
try:
    result = ""#$$% tests/dinger/notfoundscript.sh "argone"
except SystemExit as e:
    print("Error", e)

# Use the @ flag to always print(stdout)
#$@ echo "hello"     # Will print it's stdout to sys.stdout without capturing in a var

if __name__ == "main":
    print("Before the above script blocks are run")
```


###### Multiple inline pysh
```Python
# Pysh runs code in blocks that are executed in-place

# Block 0
#$ cd $HOME

stdout_block1 = ""#$ echo "first block is multiline"
#$ echo "line1"
#$ echo "line2"

# The last script block won't be run
sys.exit(1)
stdout_block2 == ""#$ echo "Second"
#$ echo "Block"
```


##### Advanced usage
```Python
# run pysh manually
from pysh import Pysh
source_file = __file__
pysher = Pysh(source_file)
blocks = pysher.findblocks()

# Run a a single block
blocks[0].run()  # Not run in-place, no stdout. Silent.

# Run script block again, and print stdout with label for block
blocks[0].runp()

# Run all wanted blocks sequentially at this point,
# and print their stdout with labels
run_blocks = [block.runp() for block in blocks
              if "/root" in block.srcs]

# Start the python interpreter with pysh on source_file
# This is the same as running pysh(__file__)
pysher.shyp()
#$ echo "pysh enabled"

# Switch to another source file and run it through pysh
pysher.pysh(__file__)

# Equivalent to above
pysher.updatesrc(__file__)
pysher.pysh()

# Get information about the script blocks at runtime
t_block = pysher.blocks[0]
print(t_block.hasrun, t_block.returncode)
print(t_block.srcs, "\n--\n", t_block.stdout)
```