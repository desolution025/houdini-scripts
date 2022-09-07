from pathlib import Path
import hou
from loguru import logger


logger.disable()


ROUGHNESS = ["roughness", "rough"]
GLOSSINESS = ["glossiness", "gloss"]


def adapt_rough(node: hou.ShopNode):
    matnet : hou.ShopNode = node.parent()
    roughnode : hou.ShopNode = node.input(6)
    if roughnode is None or roughnode.type().name() != "mtlximage":
        logger.warning(f"There is no roughness texture node connected to mtlx node or the type of the node is not matlximage in Node {matnet.name()}")
        return
    
    tex = roughnode.evalParm("file")
    if tex is None:
        logger.warning(f"There is no texture input to the surface in Node {matnet.name()}")

    tex = Path(tex).stem
    for r in ROUGHNESS:
        if r in tex:
            logger.info(f"Right Roughness Texture in node {matnet.name()}")
            return
    for g in GLOSSINESS:
        if g in tex:
            substract = matnet.createNode("mtlxsubtract")
            node.setInput(6, substract)
            substract.parm("in1").set(1)
            substract.setInput(1, roughnode)
            logger.success(f"Convert a glossiness for material: {matnet.name()}")
            return
    
    logger.warning(f"Did not match any rules in node: {matnet.name()}")


def fix_mat(node: hou.ShopNode):
    if node.type().name() != "subnet":
        logger.info(f"Node {node.name()} is not a subnet")
        return
    
    mtlxs = []
    for n in node.children():
        if n.type().name() == "mtlxstandard_surface":
            mtlxs.append(n)
    if not mtlxs:
        logger.warning(f"There is no MtlXStardard_Surface node in Node {node.name()}, ignored")
        return
    
    for mtlx in mtlxs:
        adapt_rough(mtlx)
    node.layoutChildren()


sels = hou.selectedNodes()

for n in sels:
    fix_mat(n)