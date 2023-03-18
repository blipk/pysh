# py process executor
import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from pysh.utils import repr_

shells = ("bash", "python")


class pype():
    def __init__(self, pipe_kwargs=None, base_env=None, extra_env=None):
        self.pipe_kwargs = pipe_kwargs
        self.default_shell = shells[0]
        self.base_env = base_env or os.environ.copy()
        self.extra_env = extra_env or {}

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
        env = env or {}
        # print("ZZZ", self.extra_env, env)
        env = self.base_env | env | self.extra_env
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
                 env=None,
                 timeout=None,
                 **unset_kwargs):
        self.pipe = pipe or default_pipe
        self.shell = shell
        self.srcs = srcs
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.hasrun = hasrun
        self.exectime = None  # TODO
        self.env = env
        self.timeout = timeout

    def run(self, srcs=None, pipe=None, env=None):
        pipe = pipe or self.pipe
        srcs = srcs or self.srcs
        env = env or self.env
        stdout, stderr, returncode, pid = \
            pipe.run_script(srcs, shell=self.shell, env=env, timeout=self.timeout)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.pid = pid
        self.hasrun = True
        return returncode


class ScriptException(ScriptRun, Exception):
    def __init__(self, proc, **ScriptRunI):
        self.proc = proc
        super().__init__(**ScriptRunI)
        # For debugging
        with NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(ScriptRunI["srcs"])
            trace = ScriptRunI['stderr'].decode('UTF-8').replace("<string>", f.name)
            message = f"Error running {ScriptRunI['shell']} script:\n{trace}"
            super(Exception, self).__init__(message)

        # from pprint import pprint
        # pprint(self.__dict__)
        # print(self.stdout)

    def __repr__(self):
        return repr_(self)
