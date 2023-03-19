# py process executor
import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from pysh.utils import repr_, timeit

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
                   stdout=None,
                   stderr=None,
                   stdin=None,
                   env=None,
                   raise_errors=True,
                   timeout=None,
                   raw_command=False,
                   command_args=[]):
        """ Run string source script in bash or python by passing a command_string string with the -c flag or calling a script file

            :param script: as str to pass a command string to the shell,
                        or as Path object to call a script file

            :returns: (stdout, stderr)
            :raises: error on non-zero process exit code
        """
        env = env or {}
        env = self.base_env | env | self.extra_env
        shell = shell or self.default_shell

        if type(script) == type(Path()):
            command = [shell, str(Path)]
        else:
            command = [shell, "-c", script]
        if raw_command == True:
            command = [shell]
        default_args = ("script", "shell", "pipe_kwargs",
                        "stdin", "raise_errors")
        command_args = [a for a in command_args if a not in default_args]  # set -ex
        pipe_kwargs = pipe_kwargs or self.pipe_kwargs or {}
        stdout = stdout or subprocess.PIPE
        stderr = stderr or subprocess.PIPE
        pipe_args = dict(stdout=stdout,
                         stderr=stderr,
                         stdin=stdin or subprocess.PIPE,
                         bufsize=8192,
                         shell=False,
                         env=env,
                         close_fds=True) | pipe_kwargs
        #cwd, text
        proc = subprocess.Popen(command + command_args, **pipe_args)
        try:
            stdout, stderr = proc.communicate(input=stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        if raise_errors is None:
            raise_errors = True
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
                 raise_errors=None,
                 command_args=[],
                 raw_command=False,
                 **kwargs):
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
        self.raise_errors = raise_errors
        self.command_args = command_args
        self.raw_command = raw_command
        self.stdout_pipe = kwargs.get("stdout_pipe", None)
        self.stderr_pipe = kwargs.get("stderr_pipe", None)
        self.stdin_pipe = kwargs.get("stdin_pipe", None)

    def run(self, srcs=None, pipe=None, env=None):
        pipe = pipe or self.pipe
        srcs = srcs or self.srcs
        env = env or self.env
        stdout, stderr, returncode, pid = \
            pipe.run_script(srcs,
                            shell=self.shell,
                            stdin=self.stdin_pipe,
                            stdout=self.stdout_pipe,
                            stderr=self.stderr_pipe,
                            raise_errors=self.raise_errors,
                            command_args=self.command_args,
                            raw_command=self.raw_command,
                            env=env,
                            timeout=self.timeout)
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
            trace = ScriptRunI["stderr"].decode(
                'UTF-8').replace("<string>", f.name)
            message = f"Error running {ScriptRunI['shell']} script:\n{trace}"
            super(Exception, self).__init__(message)

    def __repr__(self):
        return repr_(self)
