from pathlib import Path
import hou


def changeTexFolder(node, folder):
    parms = node.allParms()
    for parm in parms:
        pt = parm.parmTemplate()
        if isinstance(pt, hou.StringParmTemplate) and pt.stringType() == hou.stringParmType.FileReference:
            if path := parm.eval():
                parm.set(str(folder/Path(path).name))


sels = hou.selectedNodes()

folder = ""

try:
    for n in sels:
        changeTexFolder(n, folder)
except BaseException as e:
    from loguru import logger
    logger.exception(e)
    hou.ui.displayMessage('Failed to change', severity=hou.severityType.Error, details=e)

    
hou.ui.displayMessage('Completed')