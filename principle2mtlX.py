from typing import Sequence
try:
    from connect_houdini import hou
except ImportError:
    import hou
from loguru import logger

logger.level("WARNING")

COLOR_CHANNELS = ["basecolor", "transcolor", "emitcolor", "opaccolor"]
FLOAT_CHANNELS = ["metallic", "rough", "ior", "aniso", "anisodir", "reflect", "coatrough", "transdist", "sheen"]

TEX_MAPPING = {
        "basecolor": 1,
        "ior": 7,
        "rough": 6,
        "aniso": 8,
        "anisodir": 9,
        "metallic": 3,
        "reflect": 4,
        "reflecttint": 5,
        "coat": 26,
        "coatrough": 27,
        "transparency": 10,
        "transcolor": 11,
        "transdist": 12,
        "dispersion": 15,
        "sss": 17,
        "sssdist": 19,
        "ssscolor": 18,
        "sheen": 22,
        "sheentint": 23,
        "emitcolor": 37,
        "opaccolor": 38
    }

NORMAL_MAPPING = {
        "baseNormal": 40,
        "coatNormal":31
    }


def trans_surface_tex(parm: hou.Parm, mtlx: hou.Node):
    matnet : hou.ShopNode = mtlx.parent()
    path = parm.eval()
    channel_name : str = parm.name().split("_texture")[0]
    texnode : hou.Node = matnet.createNode("mtlximage", channel_name.upper())
    texnode.parm('file').set(path)

    # Set color-space
    if channel_name in FLOAT_CHANNELS:
        texnode.parm("signature").set("0")
    elif channel_name not in COLOR_CHANNELS:
        texnode.parm("signature").set("vector3")

    if channel_name.endswith("Normal"):
        normal : hou.Node = matnet.createNode("mtlxnormalmap" )
        mtlx.setInput(NORMAL_MAPPING[channel_name], normal)
        normal.setInput(0, texnode)
    else:
        mtlx.setInput(TEX_MAPPING[channel_name], texnode)


def trans_disp_tex(principle: hou.Node, mtlxdisp: hou.Node):
    matnet : hou.ShopNode = mtlxdisp.parent()
    # GETTING THE PARAMETERS VALUE
    path = principle.parm("dispTex_texture").eval()
    offset= principle.parm("dispTex_offset").eval()
    scale= principle.parm("dispTex_scale").eval()
    #CREATING DISPLACE NODES
    displace = matnet.createNode("mtlximage", "DISPLACE")
    plugdisplace = matnet.createNode("mtlxdisplacement" )
    remapdisplace = matnet.createNode("mtlxremap", "OFFSET_DISPLACE" )
    #SETTING PARAMETERS DISPLACE
    #set remap
    remapdisplace.parm("outlow").set(offset)
    remapdisplace.parm("outhigh").set(1+offset)
    #set scale displace
    plugdisplace.parm("scale").set(scale)
    #set image displace
    displace.parm("file").set(path)
    displace.parm("signature").set("0")
    #SETTING INPUTS
    mtlxdisp.setInput(0, plugdisplace)
    plugdisplace.setInput(0, remapdisplace)
    remapdisplace.setInput(0, displace)

    
def convert_mtl(principle: hou.ShopNode):
    matcontext = principle.parent()
    matsubnet : hou.ShopNode = matcontext.createNode("subnet", principle.name() + "_mtlX")

    ## DEFINE OUTPUT SURFACE
    surfaceoutput = matsubnet.createNode("subnetconnector", "surface_output")
    surfaceoutput.parm("parmname").set("surface")
    surfaceoutput.parm("parmlabel").set("Surface")
    surfaceoutput.parm("parmtype").set("surface")
    surfaceoutput.parm("connectorkind").set("output")
    
    ## DEFINE OUTPUT DISPLACEMENT
    dispoutput = matsubnet.createNode("subnetconnector", "displacement_output")
    dispoutput.parm("parmname").set("displacement")
    dispoutput.parm("parmlabel").set("Displacement")
    dispoutput.parm("parmtype").set("displacement")
    dispoutput.parm("connectorkind").set("output")
    
    #CREATE MATERIALX STANDARD
    mtlx =  matsubnet.createNode("mtlxstandard_surface", "surface_mtlx")
    surfaceoutput.setInput(0, mtlx)

    for channel in TEX_MAPPING:
        logger.debug(f'check channel {channel}')
        if principle.evalParm(channel + '_useTexture') and principle.evalParm(channel + '_texture'):
            trans_surface_tex(principle.parm(channel + "_texture"), mtlx)
        else:
            pass # TODO: trans color

    if principle.evalParm('baseBumpAndNormal_enable') and principle.evalParm('baseNormal_texture'):
        trans_surface_tex(principle.parm("baseNormal_texture"), mtlx)

    if principle.evalParm('dispTex_enable') and principle.evalParm("dispTex_texture"):
        trans_disp_tex(principle, dispoutput)
    
    matsubnet.layoutChildren()
    matsubnet.setGenericFlag(hou.nodeFlag.Material, True)


def multi_convert(*nodes: hou.ShopNode):
    for n in nodes:
        if n.type().name() == 'principledshader::2.0':
            convert_mtl(n)
            logger.info(f"Convert material {n.name()}")


multi_convert(*hou.selectedNodes())