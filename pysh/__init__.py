#!/usr/bin/python
import os
import re
import sys
from ast import literal_eval
from .shrunner import run_script, ScriptRun, ScriptException

PYSH_LINE = "#$"
PYSH_READ = f'""{PYSH_LINE}'
PYSH_EXLINE = PYSH_LINE + "$"
PYSH_EXREAD = PYSH_READ + "$"

class BashBlock(ScriptRun):
    def __init__(self, lines, position, blockindex, pysh, shell="bash"):
        self.pysh = pysh
        self.srcs = "\n".join(lines)
        self.blockindex = blockindex
        self.position = position
        self.lines = lines

    @property
    def linecount(self):
        return len(self.lines)

    def wrap(self):
        self.run()
        return self.stdout

    def runp(self):
        sname = os.path.basename(self.pysh.srcf)
        stdout = self.wrap().decode("UTF-8").strip()
        print(f"[root@pysh {sname} {self.blockindex}]$ {stdout}")

    def wrap_text(self):
        return "self.run()"

    def __repr__(self) -> str:
        classname = self.__class__.__name__
        args = ", ".join(
            [f"{k}={repr(v)}" for (k, v) in self.__dict__.items()])
        return f"{classname}({args})"


class Pysh():
    def __init__(self, srfs=__file__) -> None:
        """
        """
        self.srcf = os.path.realpath(srfs)
        self.srcs = self.readsrc()
        self.srclines = self.srcs.split("\n")
        self.cursor = 0
        self.blocks = []

    def pysh(self):
        blocks = self.findblocks()
        ret = self.shyp()

    def shyp(self, blocks=None):
        blocks = blocks or self.blocks
        output = self.srcs

        # replace blocks with their function wrapper and run pysrc
        pyshed = BashBlock(output, (0, -1), "python", pysh=self)
        pyshed.wrap()
        sys.exit(pyshed.returncode)

    def ispyshc(self, line):
        return (self.isreadblock(line)
                or line.startswith(PYSH_LINE))

    def fline(self, line):
        if self.isreadblock(line):
            line = line[line.index(PYSH_READ):]
        if self.isexternalr(line):
            line = line[line.index(PYSH_EXREAD)]
        return line.replace(PYSH_READ, "").replace(PYSH_LINE, "").strip() + "\n"

    def isexternal(self, line):
        return self.ispyshc(line) and line.startswith(PYSH_EXLINE)

    def isexternalr(self, line):
        return self.ispyshc(line) and PYSH_EXREAD in line

    def isreadblock(self, line):
        return PYSH_READ in line

    def findblocks(self, srcs=None):
        srcs = srcs or self.srcs
        srclines = srcs.split("\n")

        block_i = 0
        blocks_raw = []
        block_lines_b = ""
        block_line_c = 0
        block_start_i = None
        for i, line in enumerate(srclines):
            if not self.ispyshc(line):
                continue
            line = self.fline(line)
            if block_lines_b == "":
                block_line_c = 0
                block_start_i = i
                # assert self.isreadblock(line), f"Fail: {line}"
            else:
                if self.isexternal(line):
                    assert block_line_c == 0
            block_lines_b += line
            if i+1 == len(srclines) or not self.ispyshc(srclines[i + 1]):
                block_end_i = i
                # block_lines_b = block_lines_b.strip()
                block_position = (block_start_i, block_end_i)
                blocks_raw.append((block_lines_b, block_position, block_i))
                block_lines_b = ""
                block_line_c = 0
                block_i += 1
            block_line_c += 1

        self.blocks = [BashBlock(block, position, blockindex, pysh=self)
                       for (block, position, blockindex) in blocks_raw]
        return self.blocks

    def readsrc(self, srcf=None):
        srcs = None
        srcf = srcf or self.srcf
        with open(srcf, "r") as f:
            srcs = f.read()
        return srcs


# Function wrapper so __file__ is in caller context
def auto_pysh():
    pysher = Pysh()
    pysher.pysh()
    return pysher


pysh = auto_pysh
