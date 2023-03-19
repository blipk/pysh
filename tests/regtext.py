import sys
from pysh import pysh
pysh(__file__)

#$ echo "Pysh activated"
stdout = ""#$ echo "This is standard out"


###### General syntax

# Python comments
#$  ls .         # pysh eol comment
##$ sudo rm -rf  # disable pysh line

# run external script with double $
#$$ my_script.sh

# optionally pass arguments to it
#$$ argumentative_script.sh arg1 arg2

# Change the shell that interprets the script
# must support -c command_strings or filepath if external $$
#$!sh echo "simple"
#$!perl oysters.pl
#$$!bash script.sh
stdout = ""#$!python import time; print("The time and date", time.asctime())

if __name__ == "main":
    print("Before the above script blocks are run")

###### Multiple inline pysh

# Block 0
#$ cd $HOME

stdout_block1 = ""#$ echo "first block is multiline"
#$ echo "line1"
#$ echo "line2"

# The last script block won't be run
sys.exit(1)
stdout_block2 == ""#$ echo "Second"
#$ echo "Block"


##### Real usage

# Script your system in paralel with your python code execution
# Do anything you can in bash e.g.
#$ firefox https://news.ycombinator.com && echo "opened link in firefox"

build_service()
#$ cd ~/hosted/myservice && docker compose up

aggregate_assets()
fmpg_result = ""#$ ffmpeg -i raw_video.mkv -crf {{crf}} -o
process_assets(process_fmpg_stdout(fmpg_result))



pysher.shyp()
#$ echo "pysh enabled"

