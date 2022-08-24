from typing import Optional, Sequence, Set
from loguru import logger


try:
    from connect_houdini import hou
except ImportError:
    import hou



def read_mtls(node: hou.Node) -> Set[str]:
    """
    Extract unrepeated materials

    Args:
        node (hou.Node): FBX network to extract
    """
    valid_mtls = set()  # All path of valid materials

    children = [n for n in node.children() if n.type().name() == 'geo']
    for child in children:
        if geo_node := child.renderNode():  # Check if the network contains 0 node
            if geo_node.geometry().isValid():  # Check if the geometry is invalid
                if mtl := read_prim_mtl(child.renderNode().geometry()):
                    mtl = match_mat_rule(mtl)
                    valid_mtls.add(mtl)
                    child.parm('shop_materialpath').set("")
                    logger.debug(mtl)
                else:
                    if mtl := child.evalPram('shop_materialpath'):  # Use Obj material param if no mtl attribute on prim
                        valid_mtls.add(mtl)
                        logger.debug(mtl)
    return valid_mtls


def read_prim_mtl(geo: hou.Geometry, index_: int=0, attrib_name: str='shop_materialpath') -> Optional[str]:
    """
    Read attribute of material on special prim

    Args:
        geo (hou.Geometry): input geometry
        index_ (int, optional): index of the prim. Defaults to 0.
        attrib_name (str, optional): attribute of material. Defaults to 'shop_materialpath'.

    Returns:
        Optional[str]: value of the attribute or none when the geometry has no the attribute
    """
    if not geo.findPrimAttrib(attrib_name):
        return
    prim : hou.Prim = geo.prim(index_)
    return prim.stringAttribValue(attrib_name)


def find_mat_net(node: hou.Node) -> Optional[hou.ShopNode]:
    """Find the material network in FBX Network"""
    matnets = [n for n in node.children() if n.type().name() == 'matnet']
    if len(matnets) == 0:
        return
    if len(matnets) > 1:
        logger.warning(
            f"There is multi mat network in the node: {node.path()}"
            "Containing following nodes:"
            "/n".join(map(lambda n: n.name(), matnets)))
    return matnets[0]


def simplify_mtls(matnet: hou.ShopNode, mat_ls: Sequence[str]):
    for mat in matnet.children():
        if not mat.outputs() and mat.name() not in mat_ls:  # Check if the node is a shader node and it is a invalid node
            mat : hou.Node = mat
            matname = mat.name()
            mat.destroy()
            logger.info(f"Deleted node {matname}")


def match_mat_rule(attr: str=''):
    """Any rule for remapping attribute of material to name of the material"""
    return attr


def main(*nodes : hou.Node):
    try:
        for node in nodes:
            valid_mats = read_mtls(node)
            logger.info(valid_mats)
            logger.info(f"Number of valid materials: {len(valid_mats)}")

            mat_net = find_mat_net(node)
            assert mat_net, "Did not found the matnet"

            simplify_mtls(mat_net, valid_mats)
    except BaseException as e:
        logger.exception(e)
        hou.ui.displayMessage('Error happened when solvering, visit the log to check details')
    else:
        hou.ui.displayMessage('Processing Completed')


if __name__ == "__main__":
    sels = [n for n in hou.selectedNodes() if n.isSubNetwork()]
    main(*sels)