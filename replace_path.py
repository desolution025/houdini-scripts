from loguru import logger
from connect_houdini import hou


# WORKSPACE = hou.expandString("$HIP")
# logger.debug(f"Current workspace : {WORKSPACE}")
OLD_FOLDER = R"H:\Model\Collections\实验室工具设备"



def replace_path(parm: hou.Parm):
    path_ : str = parm.evalAsString()
    parm.set(path_.replace(OLD_FOLDER, "$HIP"))


def find_file_parm(node: hou.Node) -> hou.Parm:
    if parm := node.parm("file"):
        logger.info(f"Find image node <{node.name()}>")
        return parm


def get_all_mtlximg(node: hou.Node):
    for n in node.children():
        if p := find_file_parm(n):
            replace_path(p)


def main():
    nets : tuple[hou.Node] = hou.selectedNodes()
    for net in nets:
        get_all_mtlximg(net)


main()