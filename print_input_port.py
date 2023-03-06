from os import PathLike
from typing import List
import ujson as json
from pathlib import Path

from connect_houdini import hou
# from hou import ShopNode, selectedNodes


def input_ports(node: hou.ShopNode) -> List[str]:
    return [name for name in node.inputNames()]


def save_mapping(file: PathLike, mapping: List):
    folder = Path(file).parent
    if not folder.exists():
        folder.mkdir()
    with open(file, 'w', encoding='utf8') as j:
        json.dump(mapping, j, ensure_ascii=False, escape_forward_slashes=True, indent=4)

file = "./input_mapping/rs.json"


mat = hou.selectedNodes()[0]

save_mapping(file, input_ports(mat))