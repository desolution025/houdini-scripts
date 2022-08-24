from pathlib import Path

import hou


def isMatnet(node: hou.Node):
    return node.path() == "/mat" or isinstance(node, hou.ShopNode) or node.type().name() == "materiallibrary"


def getCurMatnet():
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
    