#!/usr/bin/python
from pysh import pype
import os
import re
import sys
import uuid
import msgpack
from pathlib import Path
from ast import literal_eval
from .pype import pype, ScriptRun, ScriptException, default_pipe
from .serializer import encode, decode

PYSH_LINE = "#$"
PYSH_READ = f'""{PYSH_LINE}'
PYSH_EXLINE = PYSH_LINE + "$"
PYSH_EXREAD = PYSH_READ + "$"

injector_imports = """import msgpack
from pathlib import Path
from pysh import Pysh, pysher, pysh, pype, encode, decode, BashBlock, ScriptException
"""

block_injector = f"""{injector_imports}
class BlockInjector():
    def __init__(self, pysher, pipe=None):
        self.pysh = pysher
        self.pipe = pipe or pype()  # keep single pipe context here
        with open("blocks.dat", "rb") as f:
            blocks = msgpack.unpackb(f.read(), object_hook=decode)
        self.blocks = blocks
        assert self.pysh.srcf == __file__ or self.pysh.srcf == Path(
            __file__), f"Injector not run from where it was injected {{self.pysh.srcf}} X{{__file__}}"
        self.pysh.blocks = self.blocks

        # Reserialize references
        for i, block in enumerate(self.blocks):
            assert self.blocks[i].serialized == True, "Block was saved without serialized flag"
            self.blocks[i].pysh = self.pysh
            blocks[i].pipe = self.pipe
            # Optionally reset

    def runblock(self, blockid):
        try:
            block = self.getblock(blockid)
            if not block:
                raise IndexError("Couldn't find block ID in block injector")
            block.run(pipe=self.pipe)
        except ScriptException as e:
            print("ScriptException", e)
            pass
        return block.stdout

    def getblock(self, blockid):
        block = next((b for b in self.blocks if b.blockid == blockid), None)
        return block

    def getblockidx(self, blockid):
        block = self.getblock(blockid)
        index = self.blocks.index(block)
        return index
block_injector = BlockInjector(pysher=Pysh(__file__))
"""


class BlockInjector():
    def __init__(self, pysher, pipe=None):
        self.pysh = pysher
        self.pipe = pipe or pype()  # keep single pipe context here
        with open("blocks.dat", "rb") as f:
            blocks = msgpack.unpackb(f.read(), object_hook=decode)
        self.blocks = blocks
        assert self.pysh.srcf == __file__ or self.pysh.srcf == Path(
            __file__), f"Injector not run from where it was injected {self.pysh.srcf} X{__file__}"
        self.pysh.blocks = self.blocks

        # Reserialize references
        for i, block in enumerate(self.blocks):
            assert self.blocks[i].serialized == True, "Block was saved without serialized flag"
            self.blocks[i].pysh = self.pysh
            blocks[i].pipe = self.pipe
            # Optionally reset

    def runblock(self, blockid):
        try:
            block = self.getblock(blockid)
            if not block:
                raise IndexError("Couldn't find block ID in block injector")
            block.run(pipe=self.pipe)
            print("stdout = ", block.stdout)
        except ScriptException as e:
            print("ScriptException", e)
            pass
        return block.stdout

    def getblock(self, blockid):
        block = next((b for b in self.blocks if b.blockid == blockid), None)
        return block

    def getblockidx(self, blockid):
        block = self.getblock(blockid)
        index = self.blocks.index(block)
        return index


class BashBlock(ScriptRun):
    def __init__(self, lines: str,
                 blockindex: int,
                 position: tuple,
                 srcf: str | Path,
                 shell="bash",
                 pysh=None,
                 pipe=default_pipe,
                 serialized=False,
                 blockid=None, **scriptrun_kwargs):
        self.blockid = blockid or str(uuid.uuid4())
        self.pysh = pysh
        self.srcf = srcf
        self.lines = lines
        self.blockindex = blockindex
        self.position = position
        self.serialized = serialized
        self.serialc = None
        super().__init__(srcs=lines, shell=shell, pipe=pipe)

    @property
    def linecount(self):
        return len(self.srcs.split("\n"))

    def run(self, *args, **kwargs):
        print("Running block", self.blockid)
        super().run(*args, **kwargs)
        # print("AAA", self.stdout.decode("UTF-8"))

    def runs(self, *args, **kwargs):
        self.run(*args, **kwargs)
        return self.stdout

    def runp(self, *args, **kwargs):
        self.run(*args, **kwargs)
        sname = os.path.basename(self.pysh.srcf)
        stdout = self.stdout.decode("UTF-8").strip()
        print(f"[root@pysh {sname} {self.blockindex}]$ {stdout}")
        return self

    def serialize(self):
        # if self.serialc:
        #     return self.serialc
        # exclude_args = ("pysh", "serialized", "pipe")
        # props = {k: v for k, v in self.__dict__.copy().items()
        #          if k not in exclude_args}
        # props = props | {"serialized": True}
        # print(props)
        # serialized = BashBlock(**props)
        # serialized.pipe = None
        # serialized.pysh = None
        # # serialized = msgpack.packb(serialized) # Don't double pack, just prep for serialization
        # self.serialc = serialized
        # print(serialized)
        return msgpack.packb(self, default=encode)


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
    def wrap_imports(self, srcs=None, blocks=None):
        srcs = srcs or self.srcs
        blocks = blocks or self.blocks

        # Inject __file__ as it's not defined passing a command_string to process
        srclines = srcs.split("\n")
        srclines.insert(2, f"__file__ = '{self.srcf}'")

        # Inject block injector
        srclines.insert(3, block_injector)

        # index and replace all pysher.shyp() and pysh(__file__) calls for nonblocking
        srclines = [srcline for srcline in srclines if "shyp(" not in srcline and "pysh(" not in srcline]
        srcsw = "\n".join(srclines)


        for block in blocks:
            # Replace whole line range
            srcsw = srcsw.replace(
                block.srcs, f"block_injector.runblock('{block.blockid}')").replace("#$ ", "")

        # replace assignment quotes
        srcsw = srcsw.replace('""block_injector', "block_injector")

        # Save blocks to serial file
        block_file = "blocks.dat"
        with open(block_file, "wb") as f:
            f.write(msgpack.packb([block
                    for block in self.blocks], default=encode))

        # print("#----#")
        # print(srcsw)
        # print("#----#")

        return (srcsw, block_file)

    def wrapped(self, srcs=None, blocks=None):
        srcs = srcs or self.srcs
        blocks = blocks or self.blocks
        srcsw, block_file = self.wrap_imports(srcs, blocks)
        return (srcsw, block_file)

    def shyp(self, blocks=None, exits=True):
        blocks = blocks or self.blocks
        # Run this script with the wrapped pysh calls and then exit
        root_script, block_file = self.wrapped()
        pyshed = BashBlock(root_script,
                           0,
                           (0, -1),
                           self.srcf,
                           shell="python",
                           pysh=self)
        pyshed.run()
        print(pyshed.stdout.decode("UTF-8"))
        Path(block_file).unlink()
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

        # Line matching
        pattern = r"(?P<block>(?P<pyvar>.*)(?P<assign>\=\s\"{2})|(?P<line>(?P<command>(?P<init>(?<!\#)\#)(?P<mode>\$+)(?P<shell>!{0,1}\w*)?)(?P<space>[\s])(?P<linecontents>.*)(?P<eol>\n)))"
        matches = re.finditer(pattern, srcs)
        assert matches, "Root source file doesn't contain any Pysh"

        from pprint import pprint
        for match in matches:
            pass
            # pprint(match)
            # pprint(match.groupdict())
            # TODO match with self.blocks below

        # BlockLine matching
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
