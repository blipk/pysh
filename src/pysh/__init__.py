#!/usr/bin/python
from os.path import realpath
from inspect import stack
from pysh import pype
import os
import re
import sys
import uuid
import shlex
import msgpack
from pathlib import Path
from ast import literal_eval

from pysh.pype import pype, ScriptException, ScriptRun, default_pipe
from pysh.serializer import encode, decode
from pysh.utils import repr_, timeit

PYSH_LINE = "#$"

injector_imports = """import os
import msgpack
from pathlib import Path
from pysh import Pysh, pysher, pysh, pype, encode, decode, BashBlock, ScriptException, timeit
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

    def runblock(self, blockid, argvarvals):
        try:
            block = self.getblock(blockid)
            if not block:
                raise IndexError("Couldn't find block ID in block injector")
            block.run(pipe=self.pipe, argvarvals=argvarvals)
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
        # keep single pipe context here
        self.pipe = pipe or pype(extra_env=env)
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

    def runblock(self, blockid, argvarvals):
        try:
            block = self.getblock(blockid)
            if not block:
                raise IndexError("Couldn't find block ID in block injector")
            block.run(pipe=self.pipe, argvarvals=argvarvals)
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
                 matches=None,
                 argvarmatches=None,
                 **scriptrun_args):
        self.blockid = blockid or str(uuid.uuid4())
        self.pysh = pysh
        self.srcf = srcf
        self.blockindex = blockindex
        self.position = position
        self.serialized = serialized
        env = env or {}
        env = env | {"PYSH_BLOCK": self.blockid}
        self.matches = matches
        self.argvarmatches = argvarmatches
        super().__init__(srcs=srcs, shell=shell, pipe=pipe, env=env, **scriptrun_args)

    @property
    def linecount(self):
        return len(self.srcs.split("\n"))

    def run(self, *args, argvarvals=[], **kwargs):
        srcsw = self.srcs
        if argvarvals or self.argvarmatches:
            assert len(argvarvals) == len(
                self.argvarmatches), "Provided runvars don't match block.argvars"
            for i, v in enumerate(self.argvarmatches):
                srcsw = srcsw.replace(v["total"], argvarvals[i])
        # print("Running block", self.blockid, self.srcf)
        super().run(srcs=srcsw, *args, **kwargs)
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
    def __init__(self, srcf, init=True, test_mode=False) -> None:
        """
        """
        self.blocks = []
        self.test_mode = test_mode
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

    def pysh(self, srcf=None, exits=True, test_mode=None):
        if test_mode:
            self.test_mode = test_mode
        if os.environ.get("PYSH_ROOT", None):
            if self.test_mode:
                print("#####PYSH_ROOT can't run Pysh.pysh() while pysh is active")
            return
        srcf = srcf or self.srcf
        self.updatesrc(srcf)
        ret = self.shyp(exits)
        return self

    def shyp(self, exits=True):
        if os.environ.get("PYSH_ROOT", None):
            if self.test_mode:
                print("#####PYSH_ROOT can't run Pysh.shyp() while pysh is active")
            return
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
                           raise_errors=False,
                           env=env)
        if self.test_mode:
            print("#####PYSH_SHIPPED")
        pyshed.run()
        # print("Pyshed stdout:", pyshed.stdout) # Should be none as piped to sys.stdout
        Path(block_file).unlink()
        if exits:
            sys.exit(pyshed.returncode)

    def wrapped(self, srcs=None, blocks=None):
        srcs = srcs or self.srcs
        blocks = blocks or self.blocks
        srcsw, block_file = self.wrap_imports(srcs, blocks)
        return (srcsw, block_file)

    def wrap_imports(self, srcs=None, blocks=None):
        srcs = srcs or self.srcs
        blocks = blocks or self.blocks

        # TODO: remove anything before the shyp() call as it will be rerun ??

        # Inject pysh header
        srclines = srcs.split("\n")
        file_injector = f"__file__ = '{self.srcf}'\n"
        header = f"{file_injector}{block_injector}\n"
        header_length = len(header)
        srcsw = header + '\n'.join(srclines)

        # TODO additional modes, assignment returns besides stdout
        next_start = None
        difference = 0
        for i, block in enumerate(blocks):
            _, spanend = block.position
            start, end = spanend
            slength = (end - start)
            block_start_m = next(
                (m for m in block.matches if "linecontents" in m and m["linecontents"]))
            if len(block_start_m["mode"]) > 1:
                extern_block = True
            length = sum(
                [len(m.get("line", "") or "")
                 for m in block.matches
                 if "linecontents" in m])
            first_match = next((m for m in block.matches if not m["pyvar"]))
            sindex = srcsw.index(first_match["block"])
            assert slength == length, f"mismatch {slength} {length}"
            args = ",".join([match['argname']
                            for match in block.argvarmatches])
            runblock = f"block_injector.runblock('{block.blockid}', argvarvals=[{args}])"
            next_start = sindex  # header_length + start_accum + start - difference
            eend = next_start+length-1
            # difference = (eend - next_start)
            # assert difference == length - 1, f"diff mismatch {difference} {length}"
            srcsw = srcsw[:next_start] + runblock + srcsw[eend:]
            # print("S2", sindex, next_start, difference, header_length, length, start_accum)

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

    def findblocks(self, srcs=None):
        if os.environ.get("PYSH_ROOT", None):
            if self.test_mode:
                print("#####PYSH_ROOT can't run Pysh.findblocks() while pysh is active")
            return
        if srcs:
            self.blocks = []
        srcs = srcs or self.srcs
        if self.blocks:
            return self.blocks

        # Extract the pysh syntax lines with regex
        pattern = r"(?P<block>(?P<pyvar>.*)(?P<assign>\=\s\"{2})|(?P<line>(?P<command>(?P<init>(?<!\#)\#)(?P<mode>\$+)(?P<smarker>!{0,1})(?P<shell>\w*)?)(?P<space>[\s]+)(?P<linecontents>.*)(?P<eol>\n)))"
        matches = re.finditer(pattern, srcs)
        assert matches, "Root source file doesn't contain any Pysh"
        matches = list(matches)

        # Group the matches into blocks
        accum = -1
        mblock_i = 0
        match_blocks = []
        for i, match in enumerate(matches):
            if not match["mode"]:
                assert match["pyvar"], "Pyvar line can't have mode"
            if not match["pyvar"]:
                assert match["mode"], "Mode line can't have pyvar"

            lstart, lend = match.span()
            if mblock_i not in match_blocks:
                match_blocks.append({"matches": []})
            match_blocks[mblock_i]["matches"].append(match)
            next_match = matches[i+1] if not i > len(matches)-2 else None
            if next_match:
                nlstart, nlend = next_match.span()
                next_match_groups = next_match.groupdict()
                if (lend != nlstart  # Doesn't immediately end
                    # Next line is a pyvar, this shouldnt really happen
                    or not next_match_groups["mode"]
                    # Pyvar should always be in next group
                    or (next_match_groups["pyvar"])
                        or (len(next_match_groups["mode"]) > 1 and not match["pyvar"])):  # Next line is extern, and this line is not assignment
                    mblock_i += 1
                    continue
            accum += 1
        match_blocks = match_blocks[0:-accum]

        # Create BashBlock objects from the block-grouped matches
        def reduce_mblocks_t(mblock):
            return "".join([str((match.groupdict()["linecontents"])) + str((match.groupdict()["eol"]))
                            for match in mblock["matches"]
                            if match.groupdict()["linecontents"] is not None])  # [:-1] # Ignore pre-pysh assignment, trim last \n
        new_blocks = []
        for i, mblock in enumerate(match_blocks):
            matches = mblock["matches"]
            sstart, send = matches[0].span()
            estart, eend = matches[-1].span()
            whole = (sstart, eend)
            matches_groups = sorted(
                [m.groupdict() | {"_span": m.span()} for m in matches], key=lambda x: x["_span"][0])
            block_start_m = next(
                (m for m in matches_groups if "linecontents" in m and m["linecontents"]))
            shell = next((mgroup for mgroup in matches_groups if mgroup["shell"] and not mgroup["assign"]), {
                         "shell": None})["shell"]
            assignment = next(
                (mgroup for mgroup in matches_groups if mgroup["assign"]), None)
            spanend = (assignment["_span"][1], eend) if assignment else whole
            position = (whole, spanend)
            block_srcs = reduce_mblocks_t(mblock)
            pattern2 = r"(?P<total>({\$(?P<argname>[\w_]+)\$}))"
            argvarmatches = re.finditer(pattern2, block_srcs)
            argvarmatches = list(argvarmatches)
            argvarmatches = [
                m.groupdict() | {"_span": m.span()} for m in argvarmatches]
            for m in matches_groups:
                assert m["block"] == m["line"] if m[
                    "line"] is not None else True, f"line doesnt match block \n{m['block']}\n{m['line']}"
            command_args = []
            raw_command=False
            if len(block_start_m["mode"] or "") > 1:
                assert len(matches_groups) == 1 or (matches_groups[0]["pyvar"] and len(matches_groups) == 2), \
                    f"Extern blocklinegroup mixed with others \n {matches_groups}"
                command_args = shlex.split(block_start_m["linecontents"])
                raw_command = True
            script_block = BashBlock(srcs=block_srcs,
                                     shell=shell,
                                     blockindex=i,
                                     position=position,
                                     srcf="#internal",
                                     pysh=self,
                                     matches=matches_groups,
                                     argvarmatches=argvarmatches,
                                     command_args=command_args,
                                     raw_command=raw_command)
            new_blocks.append(script_block)
        if self.test_mode:
            for block in new_blocks:
                print(repr_(block, incl=["position", "srcs"]))
                for match in block.matches:
                    print(repr_(match, incl=["_span", "block", "line"]))
            # sys.exit(0)

        # Assign to self if not running on an arbitrary script source
        if not srcs:
            self.blocks = new_blocks

        return new_blocks

    def __repr__(self) -> str:
        return repr_(self, ["blocks"])


if os.environ.get("PYSH_ROOT", None):
    # print("#####PYSH_ROOT no creating importable instance")

    # Function wrapper to run on call source
    def x():
        return realpath(stack()[-1].filename)
    if os.environ.get("PYSH_ROOT", None) != "1":
        pysher = Pysh(x(), init=False)
    else:
        pysher = Pysh(__file__, init=False)
    pysh = pysher.pysh
