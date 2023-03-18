# py process executor
import os
import subprocess
from pathlib import Path
from .utils import repr_

shells = ("bash", "python")


class pype():
    def __init__(self, pipe_kwargs=None, env=None):
        self.pipe_kwargs = pipe_kwargs
        self.default_shell = shells[0]
        self.env = None

    def run_script(self, script: str | Path,
                   shell=None,
                   pipe_kwargs: dict = None,
                   stdin: bytes = None,
                   env=None,
                   raise_errors=True,
                   timeout=None, *args):
        """ Run string source script in bash or python by passing a command_string string with the -c flag or calling a script file

            :param script: as str to pass a command string to the shell,
                        or as Path object to call a script file

            :returns: (stdout, stderr)
            :raises: error on non-zero process exit code
        """
        env = env or self.env or os.environ.copy()
        if type(script) == type(Path()):
            command = [shell, str(Path)]
        else:
            command = [shell, "-c", script]
        shell = shell or self.default_shell
        default_args = ("script", "shell", "pipe_kwargs",
                        "stdin", "raise_errors")
        shell_args = [a for a in args if a not in default_args]  # set -ex
        pipe_kwargs = pipe_kwargs or self.pipe_kwargs or {}
        pipe_args = dict(stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         stdin=subprocess.PIPE,
                         shell=False,
                         env=env,
                         close_fds=True) | pipe_kwargs
        #cwd, env
        # text
        proc = subprocess.Popen(command + shell_args, **pipe_args)

        stdout, stderr = proc.communicate(input=stdin, timeout=timeout)
        if raise_errors and proc.returncode:
            exc_kwargs = dict(stdout=stdout, stderr=stderr,
                              shell=shell, srcs=script)
            raise ScriptException(proc, **exc_kwargs)
        return stdout, stderr, proc.returncode, proc.pid


default_pipe = pype()


class ScriptRun():
    def __init__(self, srcs: str,
                 shell: str = shells[0],
                 returncode: int | None = None,
                 stdout: str | None = None,
                 stderr: str | None = None,
                 hasrun=False,
                 pipe=None,
                 env=None):
        self.pipe = pipe or default_pipe
        self.shell = shell
        self.srcs = srcs
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.hasrun = hasrun
        self.pid = None
        self.exectime = None  # TODO
        self.env = env

    def run(self, srcs=None, pipe=None):
        pipe = pipe or self.pipe
        srcs = srcs or self.srcs
        stdout, stderr, returncode, pid = pipe.run_script(
            srcs, shell=self.shell, env=self.env)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.pid = pid
        self.hasrun = True
        return returncode


class ScriptException(ScriptRun, Exception):
    def __init__(self, proc, **ScriptRunI):
        super().__init__(**ScriptRunI)
        super(Exception, self).__init__(
            f"Error running {ScriptRunI['shell']} script:\n{ScriptRunI['stderr'].decode('UTF-8')}")
        self.proc = proc
        # from pprint import pprint
        # pprint(self.__dict__)
        # print(self.stdout)

    def __repr__(self):
        return repr_(self)
