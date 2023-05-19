import sys
import configparser
from pkg_resources import working_set
import subprocess

config = configparser.ConfigParser()
config.read(f"{__file__}\\..\\config.ini")

REQUIRED = config['GENERAL']['MODULES'].split(', ') + []
'''Check if required modules are installed, if not, attempt to install them'''
INSTALLED = {*(pkg.key for pkg in working_set if pkg.key)}
if MISSING:=[m for m in REQUIRED if m.lower() not in INSTALLED]:
    if len(MISSING) > 1:
        print(f'MISSING MODULES {", ".join(MISSING)}. ATTEMPTING AUTO-IMPORT')
    else:
        print(f'MISSING MODULE {MISSING[0]}. ATTEMPTING AUTO-IMPORT')
    PYTHON = sys.executable
    subprocess.check_call([PYTHON, '-m', 'pip', 'install', '--upgrade', *(MISSING + [])])