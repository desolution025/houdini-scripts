from pathlib import Path
import hou


def foundmissingtex(node):
    parms = node.allParms()
    paths = set()
    for parm in parms:
        pt = parm.parmTemplate()
        if isinstance(pt, hou.StringParmTemplate) and pt.stringType() == hou.stringParmType.FileReference:
            path = parm.eval()
            if path and not Path(path).exists():
                paths.add(path)
    if paths:
        return paths

def show_missingtexs(*nodes: hou.ShopNode):
    missing = {}
    for n in nodes:
        result = foundmissingtex(n)
        if result:
            missing[n.name()] = result

    if missing:
        msg = ""
        for name, paths in missing.items():
            msg += name + ": \n"
            pathmsg = "    ".join(paths)
            msg += pathmsg + "\n"
        
        hou.ui.displayMessage(msg)
    else:
        hou.ui.displayMessage("No Texture Missing")