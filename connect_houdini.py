import sys
sys.path.append(r"C:\Program Files\Side Effects Software\Houdini 19.5.303\houdini\python3.9libs")
sys.path.append(r"C:\Program Files\Side Effects Software\Houdini 19.5.303\python39\lib\site-packages")

import hrpyc
con, hou = hrpyc.import_remote_module()


try:
    import hou
except ImportError:
    pass