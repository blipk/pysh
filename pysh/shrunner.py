shells = ("bash", "python")

def run_script(script, stdin=None, shell="bash", raise_errors=False, *args):
    """ Run string source script in bash or python by passing a command_string string with the -c flag
        :returns: (stdout, stderr)
        :raises: error on non-zero return code
    """
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
        raise ScriptException(proc.returncode, stdout, stderr, script)
    return stdout, stderr, proc.returncode

class ScriptRun():
    def __init__(self, srcs, returncode=None, stdout=None, stderr=None, shell="bash"):
        self.srcs = srcs
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.hasrun = False
        self.shell = shell

    def run(self):
        stdout, stderr, returncode = run_script(self.lines)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.hasrun = True
        return returncode

class ScriptException(ScriptRun, Exception):
    def __init__(self, returncode, stdout, stderr, script):
        Exception().__init__("Error running script")