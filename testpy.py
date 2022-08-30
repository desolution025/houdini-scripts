
from connect_houdini import hou


parms = hou.node('/obj/KB3D_SecretLab_Native_fbx/materials/AluminiumA').allParms()

for parm in parms:
    pt = parm.parmTemplate()
    if isinstance(pt, hou.StringParmTemplate): # and pt.stringType() == hou.stringParmType.FileReference:
        print(parm.name())
