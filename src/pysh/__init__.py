#!/usr/bin/python
from pysh import pype
import os
import re
import sys
import uuid
import msgpack
from pathlib import Path
from ast import literal_eval

from pysh.pype import pype, ScriptException, ScriptRun, default_pipe
from pysh.serializer import encode, decode

PYSH_LINE = "#$"
PYSH_READ = f'""{PYSH_LINE}'
PYSH_EXLINE = PYSH_LINE + "$"
PYSH_EXREAD = PYSH_READ + "$"

injector_imports = """import os
import msgpack
from pathlib import Path
from pysh import Pysh, pysher, pysh, pype, encode, decode, BashBlock, ScriptException
"""

block_injector = f"""{injector_imports}
class BlockInjector():
    def __init__(self, pysher, pipe=None):
        self.pysh = pysher
        env = {{"PYSH_RUNNING": "1"}}
        self.pipe = pipe or pype(extra_env=env)  # keep single pipe context here
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
        env = {"PYSH_RUNNING": "1"}
        self.pipe = pipe or pype(extra_env=env)  # keep single pipe context here
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
    def __init__(self, srcs: str,
                 blockindex: int,
                 position: tuple,
                 srcf: str | Path,
                 shell="bash",
                 pysh=None,
                 pipe=default_pipe,
                 serialized=False,
                 blockid=None,
                 env=None,
                 matches=None, **scriptrun_args):
        self.blockid = blockid or str(uuid.uuid4())
        self.pysh = pysh
        self.srcf = srcf
        self.blockindex = blockindex
        self.position = position
        self.serialized = serialized
        env = env or {}
        env = env | {"PYSH_BLOCK": self.blockid}
        self.matches = matches
        super().__init__(srcs=srcs, shell=shell, pipe=pipe, env=env, **scriptrun_args)

    @property
    def linecount(self):
        return len(self.srcs.split("\n"))

    def run(self, *args, **kwargs):
        # print("Running block", self.blockid, self.srcf)
        # print(self.srcs)
        super().run(*args, **kwargs)
        # print("stdout = ", self.stdout.decode("UTF-8"))

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
        return msgpack.packb(self, default=encode)

    def __repr__(self) -> str:
        classname = self.__class__.__name__
        args = ", ".join(
            [f"{k}={repr(v)}" for (k, v) in self.__dict__.items()])
        return f"{classname}({args})"


class Pysh():
    def __init__(self, srcf, init=True) -> None:
        """
        """
        self.blocks = []
        if init is not False:
            self.updatesrc(srcf)

    def readsrc(self):
        srcs = None
        with open(self.srcf, "r") as f:
            srcs = f.read()
        return srcs

    def updatesrc(self, srcf):
        self.srcf = os.path.realpath(srcf)
        self.srcs = self.readsrc()
        self.srclines = self.srcs.split("\n")
        self.blocks = self.findblocks()

    def pysh(self, srcf=None, exits=True):
        if os.environ.get("PYSH_ROOT", None):
            return # print("PYSH ALREADY RUNNING")
        srcf = srcf or self.srcf
        self.updatesrc(srcf)
        ret = self.shyp(exits)
        return self

    def shyp(self, exits=True):
        if os.environ.get("PYSH_ROOT", None):
            return # print("PYSH ALREADY RUNNING")
        # Run this script with the wrapped pysh calls and then exit
        root_script, block_file = self.wrapped()
        env = {"PYSH_ROOT": "1"}
        pyshed = BashBlock(root_script,
                           0,
                           (0, -1),
                           self.srcf,
                           shell="python",
                           pysh=self,
                           stdin_pipe=sys.stdin,
                           stderr_pipe=sys.stderr,
                           stdout_pipe=sys.stdout,
                           env=env)
        pyshed.run()
        # print("Pyshed stdout:", pyshed.stdout) # Should be none as piped to sys.stdout
        Path(block_file).unlink()
        if exits:
            sys.exit(pyshed.returncode)

    # This is for .py srcscripts only
    def wrap_imports(self, srcs=None, blocks=None):
        srcs = srcs or self.srcs
        blocks = blocks or self.blocks

        #TODO: remove anything before the shyp() call as it will be rerun ??

        srclines = srcs.split("\n")
        # Inject __file__ as it's not defined passing a command_string to process
        srclines.insert(2, f"__file__ = '{self.srcf}'")
        # Inject block injector
        srclines.insert(3, block_injector)
        srcsw = "\n".join(srclines)

        # TODO improve this
        #### externs, shell, flags/mode, assignment returns
        for block in blocks:
            # Replace whole line range
            srcsw = srcsw.replace(
                block.srcs, f"block_injector.runblock('{block.blockid}')\n").replace(PYSH_LINE + " ", "")

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

    def findblocks(self, srcs=None):
        if srcs:
            self.blocks = []
        srcs = srcs or self.srcs

        # Extract the pysh syntax lines with regex
        pattern = r"(?P<block>(?P<pyvar>.*)(?P<assign>\=\s\"{2})|(?P<line>(?P<command>(?P<init>(?<!\#)\#)(?P<mode>\$+)(?P<shell>!{0,1}\w*)?)(?P<space>[\s])(?P<linecontents>.*)(?P<eol>\n)))"
        matches = re.finditer(pattern, srcs)
        assert matches, "Root source file doesn't contain any Pysh"
        matches = list(matches)

        # Group the matches into blocks
        accum = -1
        mblock_i = 0
        match_blocks = []
        for i, match in enumerate(matches):
            lstart, lend = match.span()
            if mblock_i not in match_blocks:
                match_blocks.append({"matches": []})
            match_blocks[mblock_i]["matches"].append(match)
            next_match = matches[i+1] if not i > len(matches)-2 else None
            if next_match:
                nlstart, nlend = next_match.span()
                if lend != nlstart:
                    mblock_i += 1
                    continue
            accum += 1
        match_blocks = match_blocks[0:-accum]

        # Create BashBlock objects from the block-grouped matches
        def reduce_mblocks_t(mblock):
            return "".join([str((match.groupdict()["linecontents"]) + "\n") for match in mblock["matches"]
                        if match.groupdict()["linecontents"] is not None])
        new_blocks = []
        for i, mblock in enumerate(match_blocks):
            matches = mblock["matches"]
            sstart, send = matches[0].span()
            estart, eend = matches[-1].span()
            #TODO extract shell
            matches_groups = [match.groupdict() | {"_span": match.span()} for match in matches]
            position = (sstart, eend)
            script_block = BashBlock(srcs=reduce_mblocks_t(mblock),
                                    blockindex=i,
                                    position=position,
                                    srcf="#internal",
                                    pysh=self,
                                    matches=matches_groups)
            new_blocks.append(script_block)

        # Assign to self if not running on an arbitrary script source
        if not srcs:
            self.blocks = new_blocks

        return new_blocks


# Function wrapper to run on call source
from inspect import stack
from os.path import realpath
importer = realpath(stack()[-1].filename)
pysher = Pysh(importer, init=False)
pysh = pysher.pysh
