from typing import Set
import hou

def downstreams(node: hou.Node) -> Set[hou.Node]:
    outs : Set[hou.Node] = {node,}
    def recu_down(node: hou.Node, outs: set):
        if ds := node.outputs():
            for n in ds:
                outs.add(n)
                recu_down(n, outs)
    recu_down(node, outs)
    return outs