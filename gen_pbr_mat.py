from typing import Mapping
from os import PathLike
from pathlib2 import Path
import ujson as json
from loguru import logger
try:
    import hou
except:
    from connect_houdini import hou

mapping_file : Path = Path(__file__).parent/"input_mapping/attrbs_mapping.json"
with open(mapping_file, 'r', encoding='utf8') as j:
    CONNECT_MAPPING = json.load(j)
    
COLOR_CHANNELS = ["Diffuse", "Specular","Reflection", "Refrection", "Translucency", "Transmission", "Emission"]
FLOAT_CHANNELS = ["Metalness", "Roughness", "Glossiness", "Bump", "Height"]


def getCurMatnet() -> hou.Node:
    """Find active matnet"""
    panes :tuple[hou.PaneTab] = [p for p in hou.ui.currentPaneTabs() if isinstance(p, hou.NetworkEditor) and p.pwd().isMaterialManager()]

    # return /mat if no active matnet
    if not panes:
        return hou.node("/mat")

    cur = [n for n in panes if n.isCurrentTab()]

    # return the first matnet if all/no matnet is active
    if len(cur) == len(panes) or len(cur) == 0:
        return panes[0].pwd()

    # return the matnet which was first found
    return cur[0].pwd()


def gen_karma(parent: hou.Node, name: str, texs: Mapping[str, PathLike]):
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

    # Create MaterialX Standard
    mtlx : hou.Node =  matnet.createNode("mtlxstandard_surface", "surface_mtlx")
    surfaceoutput.setInput(0, mtlx)

    # Set Texture Coord
    tex_coord : hou.Node = matnet.createNode("mtlxtexcoord", "TexCoord")
    tex_coord.parm("signature").set("vector2")

    tex_mul : hou.Node = matnet.createNode("mtlxmultiply", "CoordMultiply")
    tex_mul.parm("signature").set("vector2")

    tex_add : hou.Node = matnet.createNode("mtlxadd", "CoordAdd")
    tex_add.parm("signature").set("vector2")

    tex_add.setInput(0, tex_mul)
    tex_mul.setInput(0, tex_coord)

    # Set surface channels for material
    mtlx_mapping = CONNECT_MAPPING["MtlX"]

    for channel in mtlx_mapping:
        # Normal 
        if channel == "Normal" and "Normal" in texs:
            normal = matnet.createNode("mtlximage", "Normal")
            normal.parm("signature").set("vector3")
            plugnormal : hou.Node = matnet.createNode("mtlxnormalmap" )
            normal.parm("file").set(str(texs["Normal"]))
            mtlx.setInput(mtlx.inputIndex(mtlx_mapping["Normal"]), plugnormal)
            plugnormal.setInput(0, normal)
            normal.setInput(1, tex_add)

        # Invert Glossiness
        elif channel == "Roughness" and "Roughness" not in texs and "Glossiness" in texs:
            gloss = matnet.createNode("mtlximage", "Glossiness")
            gloss.parm("signature").set("0")
            substract = matnet.createNode("mtlxsubtract" )
            gloss.parm("file").set(str(texs["Glossiness"]))
            mtlx.setInput(mtlx.inputIndex(mtlx_mapping["Roughness"]), substract)
            substract.parm("in1").set(1)
            substract.setInput(1, gloss)
            gloss.setInput(1, tex_add)

        elif channel in texs:
            img : hou.Node = matnet.createNode("mtlximage", channel)
            img.parm("file").set(str(texs[channel]))
            mtlx.setInput(mtlx.inputIndex(mtlx_mapping[channel]), img)
            if channel in FLOAT_CHANNELS:
                img.parm("signature").set("0")
            elif channel not in COLOR_CHANNELS:
                img.parm("signature").set("vector")
            img.setInput(1, tex_add)

        if "Emission" in texs:
            mtlx.parm("emission").set(1.0)
        
    # Set displacement
    if "Displacement" in texs:

        # Define output displacement
        dispoutput : hou.Node = matnet.createNode("subnetconnector", "displacement_output")
        dispoutput.parm("parmname").set("displacement")
        dispoutput.parm("parmlabel").set("Displacement")
        dispoutput.parm("parmtype").set("displacement")
        dispoutput.parm("connectorkind").set("output")

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

        displace.setInput(1, tex_add)
    
    matnet.layoutChildren()
    matnet.setGenericFlag(hou.nodeFlag.Material, True)
    logger.success(f"Create Material {name} in {matnet.path()}")
    return matnet

def gen_karmas(textures: Mapping[str, Mapping[str, PathLike]]):
    parent = getCurMatnet()
    mats = []
    num_mats = len(textures)
    try:
        with hou.InterruptableOperation("Generate karma materials", long_operation_name="Parsing texture files", open_interrupt_dialog=True) as operation:
            for name, texs in textures.items():
                mat = gen_karma(parent, name, texs)
                mats.append(mat)
                operation.updateLongProgress((len(mats)-1) / num_mats, f"Creating material {len(mats)} : {mat.name()}")
    except hou.OperationInterrupted:
        parent.deleteItems(tuple(mats))
    else:
        parent.layoutChildren(items=mats)
        hou.ui.displayMessage(f"Create {len(textures)} Material(s) in {parent.name()}")
    # mats = [gen_karma(parent, name, texs) for name, texs in textures.items()]
    # logger.info(f"Create {len(textures)} Material(s) in {parent.name()}")


# Give up for now until RS gets better
"""
def gen_rs(parent: hou.Node, name: str, texs: Mapping[str, PathLike]):
    # Generate rs material builder
    rsbuilder : hou.ShopNode = parent.createNode("rs_usd_material_builder", name)

    # Find material and usd node
    for n in rsbuilder.children():
        if n.type().name() == "redshift::StandardMaterial":
            rsstd : hou.ShopNode = n
        elif n.type().name() == "redshift_usd_material":
            rsusd : hou.ShopNode = n

    # Set surface channels for material
    rs_mapping = CONNECT_MAPPING["Redshift"]
    
    # convert glossiness to roughness
    if "Roughness" not in texs and "Glossiness" in texs:
        rs_mapping["Glossiness"] = rs_mapping["Roughness"]
        del rs_mapping["Roughness"]

        rsstd.parm("refl_isGlossiness").set(1)
        rsstd.parm("refr_isGlossiness").set(1)

    # Only use normal or bump
    if "Normal" in texs and "Bump" in texs:
        del texs["bump"]

    for channel in rs_mapping:
        if channel not in texs:
            continue

        # Create Texture Node
        if channel != "Opacity":
            tex : hou.Node = rsbuilder.createNode("redshift::TextureSampler", channel)
            tex.parm("tex0").set(str(texs[channel]))

        # Normal or Bump
        if channel == "Normal" or channel == "Bump":
            tex.parm("tex0_colorSpace").set("raw")
            bumpNode = rsbuilder.createNode("redshift::BumpMap")

            if channel == "Normal":
                bumpNode.parm("inputType").set("1")                

            rsstd.setNamedInput("bump_input", bumpNode, "out")
            bumpNode.setNamedInput("input", tex, "outColor")

        # Opacity
        elif channel == "Opacity":
            spriteNode : hou.ShopNode = rsbuilder.createNode("redshift::Sprite")
            spriteNode.setNamedInput("input", rsstd, "outColor")
            rsusd.setNamedInput("Surface", spriteNode, "outColor")
            spriteNode.parm("tex0").set(str(texs[channel]))

        # Roughness
        elif channel == "Roughness" or channel == "Glossiness":
            tex.parm("tex0_colorSpace").set("raw")
            rampNode = rsbuilder.createNode("redshift::RSRamp")
            rampNode.setNamedInput("input", tex, "outColor" )                
            rsstd.setNamedInput("refl_roughness", rampNode, "outColor")

        # Metalness
        elif channel == "Metalness":
            tex.parm("tex0_colorSpace").set("raw")
            channelSplitter2 = rsbuilder.createNode("redshift::RSColorSplitter")
            rsstd.setNamedInput("metalness", channelSplitter2, "outR")
            channelSplitter2.setNamedInput("input", tex, "outColor" )

        # Common
        else:
            rsstd.setNamedInput(rs_mapping[channel], tex, "outColor")
            if channel not in COLOR_CHANNELS:
                tex.parm("tex0_colorSpace").set("raw")

            # Translucency
            if channel == "Translucency":
                rsstd.parm("refr_thin_walled").set(1)
                rsstd.parm("ms_amount").set(0.5)


    # Set displacement
    if "Displacement" in texs:
        tex : hou.Node = rsbuilder.createNode("redshift::TextureSampler", channel)            
        tex.parm("tex0").set(str(texs["Displacement"]))
        dispNode = rsbuilder.createNode("redshift::Displacement")


        rsusd.setNamedInput("Displacement", dispNode, "out")
        dispNode.setNamedInput("texMap", tex, "outColor")
    

    rsbuilder.layoutChildren()
    # rsbuilder.setGenericFlag(hou.nodeFlag.Material, False)
    logger.info(f"Create Material {name} in {rsbuilder.path()}")


    return rsbuilder


def gen_collect(*nodes: hou.ShopNode, parent: hou.ShopNode, name: str) -> hou.SopNode:
    collect : hou.ShopNode = parent.createNode("collect", name)
    for i, n in enumerate(nodes):
        collect.setInput(i, n, 0)
        n.setGenericFlag(hou.nodeFlag.Material, False)
    
    parent.layoutChildren(collect, *nodes)


def copy_spare_parms(origin: hou.Node, target: hou.Node):
    ptg :hou.ParmTemplateGroup = origin.parmTemplateGroup()
    if origin.type().name() == "mtlxstandard_surface":
        ptg.remove("signature")
    if inputnum_parm := target.parmTemplateGroup().find("inputnum"):
        ptg.append(inputnum_parm)
    target.setParmTemplateGroup(ptg)
"""


if __name__ == "__main__":
    folder = hou.ui._selectFile(title="Choose textures directory", file_type=hou.fileType.Directory, chooser_mode=hou.fileChooserMode.Read)
    from auto_gen_pbr import PBR_Tex_Folder
    dd, va = PBR_Tex_Folder(folder).makeup_mtl()

    gen_karmas(dd)