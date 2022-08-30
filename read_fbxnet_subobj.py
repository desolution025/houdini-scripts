# Use this in a python-sop node


from typing import Optional, Tuple, Set
import hou


node = hou.pwd()
geo = node.geometry()



fbx_network : str = hou.parm("../../../../objpath").eval()

subobjs = [n for n in hou.node(fbx_network).children() if n.type().name() == 'geo' and not n.inputs()]  # All top upstream geo node in fbx network


def downstreams(node: hou.Node) -> Set[hou.Node]:
    outs : Set[hou.Node] = {node,}
    def recu_down(node: hou.Node, outs: set):
        if ds := node.outputs():
            for n in ds:
                outs.add(n)
                recu_down(n, outs)
    recu_down(node, outs)
    return outs

