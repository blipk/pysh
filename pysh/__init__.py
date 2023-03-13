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
    def __init__(self, lines, blockindex, position, srcfscript, pysh, shell="bash"):
        self.pysh = pysh
        self.srcf = srcfscript
        self.lines = lines
        self.srcs = "\n".join(lines)
        super().__init__(srcs=self.srcs)
        self.blockindex = blockindex
        self.position = position

    @property
    def linecount(self):
        return len(self.lines)

    def runp(self):
        sname = os.path.basename(self.pysh.srcf)
        stdout = self.wrap().decode("UTF-8").strip()
        print(f"[root@pysh {sname} {self.blockindex}]$ {stdout}")
        return self

    # Python shell only functions - for pysh autoembed
    def wrap(self):
        # generate a function and inject into source before shyp()
        wrapper = BashBlock(**self)
        wrapper.wrapped()
        self.run()
        return self.returncode

    def wrap_imports(self):
        # import trimmed pysh
        pass

    def wrapped(self, srcs = None):
        # the generated code
        srcs = srcs or self.srcs
        srcsw = ""
        return srcsw

    def __repr__(self) -> str:
        classname = self.__class__.__name__
        args = ", ".join(
            [f"{k}={repr(v)}" for (k, v) in self.__dict__.items()])
        return f"{classname}({args})"


class Pysh():
    def __init__(self, srcf=__file__) -> None:
        """
        """
        self.srcf = os.path.realpath(srcf)
        self.srcs = self.readsrc()
        self.srclines = self.srcs.split("\n")
        self.blocks = []
        # self.cursor = 0

    def updatesrc(self, srcf):
        self.srcf = srcf
        self.srcs = self.readsrc()
        self.srclines = self.srcs.split("\n")
        self.blocks = []

    def pysh(self, srcf=None):
        srcf = srcf or self.srcf

        blocks = self.findblocks()
        ret = self.shyp()
        return self

    def shyp(self, blocks=None):
        blocks = blocks or self.blocks
        #TODO index and replace all pysh() calls for nonblocking

        # Run this script with the wrapped pysh calls and then exit
        pyshed = BashBlock(self.srcs,
                           0,
                           (0, -1),
                           self.srcf,
                           shell="python",
                           pysh=self)

        # pyshed.wrapped()
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
        block_t = ""
        block_line_c = 0
        block_start_i = None
        for i, line in enumerate(srclines):
            if not self.ispyshc(line):
                continue
            line = self.fline(line)
            if block_t == "":
                block_line_c = 0
                block_start_i = i
                # assert self.isreadblock(line), f"Fail: {line}"
            else:
                if self.isexternal(line):
                    assert block_line_c == 0
            block_t += line
            if i+1 == len(srclines) or not self.ispyshc(srclines[i + 1]):
                block_end_i = i
                # block_t = block_t.strip()
                block_position = (block_start_i, block_end_i)
                blocks_raw.append((block_t, block_i, block_position))
                block_t = ""
                block_line_c = 0
                block_i += 1
            block_line_c += 1

        self.blocks = [BashBlock(block_t, blockindex, position,
                                 self.srcf,
                                 pysh=self)
                       for (block_t, blockindex, position) in blocks_raw]
        return self.blocks

    def readsrc(self, srcf=None):
        srcs = None
        srcf = srcf or self.srcf
        with open(srcf, "r") as f:
            srcs = f.read()
        return srcs


# Function wrapper to run on call source
pysher = Pysh()
pysh = pysher.pysh
