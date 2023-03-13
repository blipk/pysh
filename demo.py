#!/usr/bin/python

from pysh import pysh

# run pysh whenever this file is interpreted
pysh(__file__)
#$ echo "Pysh activated"

# run pysh manually
from pysh import Pysh
source_file = __file__
p = Pysh(source_file)
blocks = p.findblocks()

# Run all blocks and print their stdout
run_blocks = [block.runp() for block in blocks]
# Run a a single block and silently
blocks[0].run()

# Start the python interpreter with pysh on source_file
p.shyp()

# Example usage
#$ ls . # comment
##$ xdg-open . # double comment to disable in pysh
#$$ my_script.sh arg1 arg2 # run a bash script and pass arguments to it with double $

# Script your system in paralel with your python code execution
##$ firefox https://news.ycombinator.com && echo "opened link in firefox"
##$ cd ~/hosted/myservice && docker compose up
##$ ffmpeg -i -crf


# Save an inline or external scripts stdout to a variable in your python - computed at python runtime
stdout = ""#$ echo "non-stdout"
print(stdout)
#>non-stdout

stdout = ""#$ echo "multiline"
#$ echo "l1"
#$ echo "l2"
#$ echo "l3"
print(stdout)
#> multiline
#>l1
#>l2
#>l3