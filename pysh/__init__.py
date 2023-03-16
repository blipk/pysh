#!/usr/bin/python
import os
import re
import sys
import msgpack
from ast import literal_eval
from .pype import run_script, ScriptRun, ScriptException

PYSH_LINE = "#$"
PYSH_READ = f'""{PYSH_LINE}'
PYSH_EXLINE = PYSH_LINE + "$"
PYSH_EXREAD = PYSH_READ + "$"


class BashBlock(ScriptRun):
    def __init__(self, lines,
                 blockindex,
                 position,
                 srcfscript,
                 pysh,
                 shell="bash",
                 serialized=False):
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
        self.run()
        sname = os.path.basename(self.pysh.srcf)
        stdout = self.stdout.decode("UTF-8").strip()
        print(f"[root@pysh {sname} {self.blockindex}]$ {stdout}")
        return self

    def runs(self):
        self.run()
        return self.stdout

    def serialized(self):
        props = {k: v for k, v in self.__dict__
                 if k not in ("pysh", "serialized")}
        props = props | {"serialized": True}
        serialized = BashBlock(**props)
        serialized = msgpack.dumps(serialized)
        return serialized

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
        # self.cursor = 0 # TODO

    def readsrc(self, srcf=None):
        srcs = None
        srcf = srcf or self.srcf
        with open(srcf, "r") as f:
            srcs = f.read()
        return srcs

    def updatesrc(self, srcf):
        self.srcf = srcf
        self.srcs = self.readsrc()
        self.srclines = self.srcs.split("\n")
        self.blocks = []

    def pysh(self, srcf=None, exits=True):
        srcf = srcf or self.srcf
        blocks = self.findblocks()
        ret = self.shyp(exits)
        return self

    # This is for .py srcscripts only
    def wrap_imports(self, srcs=None):
        srcs = self.srcs or None
        # import trimmed pysh
        # inject blocks (serialize to with tmpfile and msgpack)
        #(?P<block>(?P<blockline>(?P<blockstart>(?<!\#)\#\$+(?P<shell>!*\w*))(?P<pyshstart>[\s])(?P<blockcontents>.*)(?P<eolblock>[\n[^\n]]\s*\#.*)*))
        #(?P<block>(?P<blockline>(?P<blockstart>(?<!\#)\#\$+(?P<shell>!*\w*))(?P<pyshstart>[\s])(?P<blockcontents>.*)))
        #(?P<block>(?P<blockline>(?P<blockstart>(?<!\#)\#\$+(?P<shell>!*\w*))(?P<pyshstart>[\s])(?P<blockcontents>.*)*))
        #(?P<block>(?P<blockline>(?P<blockstart>(?<!\#)\#\$+(?P<shell>!*\w*))(?P<pyshstart>[\s])(?P<linecontents>.*)(?P<eol>\n)))
        #(?P<block>(?P<blockline>(?P<pyvar>.*\"*)(?P<blockstart>(?<!\#)\#\$+(?P<shell>!*\w*))(?P<pyshstart>[\s])(?P<linecontents>.*)(?P<eol>\n)))
        #(?P<block>(?P<pyvar>.*\"*)(?P<line>(?P<command>(?<!\#)\#\$+(?P<shell>!*\w*))(?P<space>[\s])(?P<linecontents>.*)(?P<eol>\n)))

        #(?P<block>(?P<pyvar>.*)(?P<line>(?P<command>(?<!\#)\#\$+(?P<shell>!*\w*))(?P<space>[\s])(?P<linecontents>.*)(?P<eol>\n)))
        #(?P<block>(?P<pyvar>.*)(?P<line>(?P<command>(?<!\#)\#\$+(?P<shell>!{0,1}\w*))(?P<space>[\s])(?P<linecontents>.*)(?P<eol>\n)))
        #(?P<block>(?P<pyvar>.*)(?P<assign>\=\s\"{2})|(?P<line>(?P<command>(?P<init>(?<!\#)\#)(?P<mode>\$+)(?P<shell>!{0,1}\w*))(?P<space>[\s])(?P<linecontents>.*)(?P<eol>\n)))

        # Check pyvar is valid assignment "" - otherwise just run
        pattern = r"(?P<block>(?P<pyvar>.*)(?P<assign>\=\s\"{2})|(?P<line>(?P<command>(?P<init>(?<!\#)\#)(?P<mode>\$+)(?P<shell>!{0,1}\w*)?)(?P<space>[\s])(?P<linecontents>.*)(?P<eol>\n)))"
        # pysh_blocks = r"(?P<block>[^\#]\#\$.*)"
        # pysh_comments = r"(?P<block>\#\#\$.*)"
        # pysh_extern = r""

        matches = re.finditer(pattern, srcs)
        assert matches, "Root source file doesn't contain any Pysh"

        from pprint import pprint
        for match in matches:
            pprint(match)
            pprint(match.groupdict())
        # generate a function wrapper for each block and place at its position
        # ? id the blocks
        # ? string replace with id marker? that references self.blocks.keyed()
        # self.blocks[id].runs() # use BlockWrapper.get(id).run() instead?

        # TODO index and replace all pysh() calls for nonblocking
        return None

    def wrapped(self, srcs=None):
        srcs = srcs or self.srcs
        srcsw = self.wrap_imports(srcs)
        return srcsw

    def shyp(self, blocks=None, exits=True):
        blocks = blocks or self.blocks
        # Run this script with the wrapped pysh calls and then exit
        pyshed = BashBlock(self.wrapped(),
                           0,
                           (0, -1),
                           self.srcf,
                           shell="python",
                           pysh=self)
        pyshed.run()
        if exits:
            sys.exit(pyshed.returncode)

    def blockinfo(self, blocks: list[BashBlock] = None):
        blocks = blocks or self.blocks
        block_info = [
            {block.srcs: ""}
            for block in blocks
        ]

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


# Function wrapper to run on call source
pysher = Pysh()
pysh = pysher.pysh
