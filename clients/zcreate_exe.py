import shutil
import os
from glob import glob

while 1:
    useless = glob("*.spec")
    payload = raw_input("Enter Full File Name:  ")

    if os.path.isfile(payload):
        icon = raw_input("If you wants to add custom icon to payload then ENTER ITs PATH:  ")
        if icon and os.path.isfile(icon):
            os.system('pyinstaller --onefile -w "%s" -i "%s"' % (payload, icon))
        else:
            os.system('pyinstaller --onefile -w "%s"' % (payload))
        break

shutil.rmtree('build')
for f in useless:
    os.remove(f)

raw_input("Press Enter to Continue ...")
