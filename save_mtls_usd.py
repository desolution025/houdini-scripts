from typing import Sequence
import hou
from hou import LopNode, TopNode
from loguru import logger


def set_wedge(lopnode: LopNode, topnet: TopNode):
    prims : Sequence[str] = [p.GetName() for p in lopnode.stage().GetPrimAtPath("/materials").GetChildren()]
    primcount = len(prims)
    logger.info(f"Found {primcount} material primtives to output")

    wedge : TopNode = topnet.createNode('wedge', "mtls_wedge")

    wedge.parm("wedgecount").set(primcount)
    wedge.parm("wedgeattributes").set(1)
    wedge.parm("name1").set("mtl_wedge")
    wedge.parm("type1").set(4)
    wedge.parm("values1").set(primcount)
    for i, prim in enumerate(prims):
        wedge.parm(f"strvalue1_{i+1}").set(prim)

    topnet.layoutChildren(wedge)
    return wedge


def findtopnet(lopnet: LopNode):
    topnets = [n for n in lopnet.children() if n.type().name() == "topnet"]
    if topnets:
        logger.info(f"Use the topnet {topnets[0].name()} to generate wedge")
        return topnets[0]
    else:
        topnet = lopnet.createNode("topnet")
        lopnet.layoutChildren(topnet)
        logger.info(f"No topnet in the current LopNetwork, auto generate topnet named {topnet.name()}")
        return topnet


matlops = [n for n in hou.selectedNodes() if n.type().name() == "materiallibrary"]
if not matlops:
    hou.ui.displayMessage("Need to select one materaillibrary lopnode to generate wedge", severity=hou.severityType.Warning)
else:
    try:
        matlib = matlops[0]
        wedgenode = set_wedge(matlib, findtopnet(matlib.parent()))
    except BaseException as e:
        logger.exception(e)
    else:
        hou.ui.displayMessage(f"Generated wedge node: {wedgenode.path()}")