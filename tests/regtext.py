from pysh import pysh
pysh(__file__)

#$@ echo "simple"

#$@!sh echo "simple"
#$%@!sh echo "simple"

#$!@sh echo
#$@%!sh echo
#$@% echo

#$!sh echo "simple"

#$ echo "Pysh activated"
stdout = ""#$ echo "This is standard out"



# Python comments
#$  ls .         # pysh eol comment
##$ sudo rm -rf  # disable pysh line

#$ cd $HOME

#$$ my_script.sh
#$$ argumentative_script.sh arg1 arg2

#$@sh echo "simple"

#$!sh echo "simple"
#$!perl oysters.pl
#$$!bash script.sh
stdout = ""#$!python import time; print("The time and date", time.asctime())

if __name__ == "main":
    print("Before the above script blocks are run")


stdout_block1 = ""#$ echo "first block is multiline"
#$ echo "line1"
#$ echo "line2"

# The last script block won't be run
sys.exit(1)
stdout_block2 == ""#$ echo "Second"
#$ echo "Block"



build_service()
#$ cd ~/hosted/myservice && docker compose up

aggregate_assets()
fmpg_result = ""#$ ffmpeg -i raw_video.mkv -crf {{crf}} -o
process_assets(process_fmpg_stdout(fmpg_result))

pysher.shyp()
#$ echo "pysh enabled"

