from typing import Mapping
from os import PathLike
from loguru import logger
import hou

def isMatnet(node: hou.Node):
    return node.path() == "/mat" or isinstance(node, hou.ShopNode) or node.type().name() == "materiallibrary"


def getCurMatnet() -> hou.Node:
    """Find active matnet"""
    panes :tuple[hou.PaneTab] = [p for p in hou.ui.currentPaneTabs() if isinstance(p, hou.NetworkEditor) and isMatnet(p.pwd())]

    # return /mat if no active matnet
    if not panes:
        return hou.node("/mat")

    cur = [n for n in panes if n.isCurrentTab()]

    # return the first matnet if all/no matnet is active
    if len(cur) == len(panes) or len(cur) == 0:
        return panes[0].pwd()

    # return the matnet which was first found
    return cur[0].pwd()
    
COLOR_CHANNELS = ["Diffuse", "Specular", "Translucency", "Transmission", "Emisson"]
FLOAT_CHANNELS = ["Metalness", "Roughness", "Glossiness", "Bump", "Height"]

CONNECT_MAPPING = {
    "MtlX": {
        "Diffuse": 1,
        "Specular": 5,
        "Metalness": 3,
        "Roughness": 6,
        "Normal": 40,
        "Opacity": 38,
        "Translucency": 11,
        "Transmission": 10,
        "Emission": 37
    }
}


def gen_mat(parent: hou.Node, name: str, texs: Mapping[str, PathLike]):
    # Generate material subnetwork
    matnet : hou.Node = parent.createNode("subnet", name)
    
    # Set Karma MeterialX Mask
    mask_parm = hou.StringParmTemplate("tabmenumask", "TabMenuMask", 1)
    parmfolder = hou.FolderParmTemplate("folder1", "KARMA MASK", ((mask_parm,)), hou.folderType.Collapsible)
    parmgroup = hou.ParmTemplateGroup((parmfolder,))

    matnet.setParmTemplateGroup(parmgroup)
    matnet.parm("tabmenumask").set("MaterialX parameter collect subnet null subnetconnector karma USD")

    # Define ouput surface
    surfaceoutput : hou.Node = matnet.createNode("subnetconnector", "surface_output")
    surfaceoutput.parm("parmname").set("surface")
    surfaceoutput.parm("parmlabel").set("Surface")
    surfaceoutput.parm("parmtype").set("surface")
    surfaceoutput.parm("connectorkind").set("output")

    # Define output displacement
    dispoutput : hou.Node = matnet.createNode("subnetconnector", "displacement_output")
    dispoutput.parm("parmname").set("displacement")
    dispoutput.parm("parmlabel").set("Displacement")
    dispoutput.parm("parmtype").set("displacement")
    dispoutput.parm("connectorkind").set("output")

    # Create MaterialX Standard
    mtlx : hou.Node =  matnet.createNode("mtlxstandard_surface", "surface_mtlx")
    surfaceoutput.setInput(0, mtlx)

    # Set surface channels for material
    mtlx_mapping = CONNECT_MAPPING["MtlX"]

    for channel in mtlx_mapping:
        # Normal 
        if channel == "Normal" and "Normal" in texs:
            normal = matnet.createNode("mtlximage", "Normal")
            normal.parm("signature").set("vector3")
            plugnormal = matnet.createNode("mtlxnormalmap" )
            normal.parm("file").set(str(texs["Normal"]))
            mtlx.setInput(mtlx_mapping["Normal"], plugnormal)
            plugnormal.setInput(0, normal)

        elif channel == "Roughness" and "Roughness" not in texs and "Glossiness" in texs:
            gloss = matnet.createNode("mtlximage", "Glossiness")
            gloss.parm("signature").set("0")
            substract = matnet.createNode("mtlxsubtract" )
            gloss.parm("file").set(str(texs["Glossiness"]))
            mtlx.setInput(mtlx_mapping["Roughness"], substract)
            substract.parm("in1").set(1)
            substract.setInput(1, gloss)

        elif channel in texs:
            img : hou.Node = matnet.createNode("mtlximage", channel)
            img.parm("file").set(str(texs[channel]))
            mtlx.setInput(mtlx_mapping[channel], img)
            if channel in FLOAT_CHANNELS:
                img.parm("signature").set("0")
            elif channel not in COLOR_CHANNELS:
                img.parm("signature").set("vector")
        
    # Set displacement
    if "Displacement" in texs:
        #CREATING DISPLACE NODES
        displace = matnet.createNode("mtlximage", "Displacement")
        plugdisplace = matnet.createNode("mtlxdisplacement" )
        remapdisplace = matnet.createNode("mtlxremap", "Offset_Displacement" )
        #SETTING PARAMETERS DISPLACE
        #set remap
        remapdisplace.parm("outlow").set(-0.5)
        remapdisplace.parm("outhigh").set(0.5)
        #set scale displace
        plugdisplace.parm("scale").set(0.1)
        #set image displace
        displace.parm("file").set(str(texs["Displacement"]))
        displace.parm("signature").set("0")
        
        #SETTING INPUTS
        dispoutput.setInput(0, plugdisplace)
        plugdisplace.setInput(0, remapdisplace)
        remapdisplace.setInput(0, displace)
    
    matnet.layoutChildren()
    logger.info(f"Create Material {name} in {matnet.path()}")
    return matnet

def gen_mats(textures: Mapping[str, Mapping[str, PathLike]]):
    parent = getCurMatnet()
    mats = [gen_mat(parent, name, texs) for name, texs in textures.items()]
    parent.layoutChildren(items=mats)