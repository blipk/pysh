# py process executor
shells = ("bash", "python")


def run_script(script, stdin=None, shell=None, raise_errors=False, *args):
    """ Run string source script in bash or python by passing a command_string string with the -c flag
        :returns: (stdout, stderr)
        :raises: error on non-zero return code
    """
    shell = shell or shells[0]
    # os.system("bash tmpfile2")
    import subprocess
    default_args = ("shell", "stdin")
    # set -e
    # set -x
    proc = subprocess.Popen([shell, "-c", script] + [a for a in args if a not in default_args],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if raise_errors and proc.returncode:
        raise ScriptException(proc.returncode, stdout, stderr, script, shell)
    return stdout, stderr, proc.returncode


class ScriptRun():
    def __init__(self, srcs: str,
                 returncode: int | None = None,
                 stdout: str | None = None,
                 stderr: str | None = None,
                 shell: str | None = None,
                 init = None):
        # if init:
        #     assert type(init) == ScriptRun
        #     return ScriptRun(init)
        self.srcs = srcs
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.hasrun = False
        self.shell = shell or shells[0]
        self.exectime = None  # TODO

    def run(self, returnc=True):
        assert self.srcs
        stdout, stderr, returncode = run_script(self.lines, shell=self.shell)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.hasrun = True
        run_result = (returncode if returnc
        else dict(
            o=stdout,
            e=stderr,
            r=returncode
        ))
        return run_result


class ScriptException(ScriptRun, Exception):
    def __init__(self, ScriptRunI):
        ScriptRun().__init(**ScriptRunI.__dict__)
        Exception().__init__("Error running script")
