from connect_houdini import hou

# parms = hou.node('/obj/KB3D_SecretLab_Native_fbx/materials/AluminiumA').allParms()

# for parm in parms:
#     pt = parm.parmTemplate()
#     # print(isinstance(pt, hou.StringParmTemplate))
#     if isinstance(pt, hou.StringParmTemplate): # and pt.stringType() == hou.stringParmType.FileReference:
#         print(parm.name())
aa : hou.ParmTemplate = hou.parm('/obj/geo1/null1/imagepath').parmTemplate()
print(aa.stringType())
print(aa.stringType() == hou.stringParmType.FileReference)