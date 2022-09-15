from os import PathLike
try:
    from connect_houdini import hou
except ImportError:
    import hou
from hou import Node
from PySide2 import QtGui
from loguru import logger


def add_asset(name: str, path: PathLike, thumbnail_path: PathLike):
    # read in the thumbnail
    thumbnail = QtGui.QImage()
    thumbnail.load(thumbnail_path)

    # add the database entry
    item_uuid = hou.qt.AssetGallery.addAsset(
        name,
        path,
        thumbnail)
    logger.success(f'insert a new asset uuid: {item_uuid}')


# set the db file to be something specific
hou.qt.AssetGallery.setAssetDBFile("d:/myproject/MyProject_AssetGalleryDb.db")

from pathlib2 import Path
assetname = hou.parm('/stage/part_info/partname').eval()
folder = Path(r"F:/3D Models\Model Pack/KitBash3D/Kitbash3D-Edo Japan/usd")
usdpath : Path = folder/(assetname + ".usd")
thumbnailpath : Path= folder/(assetname + "_thumbnail.png")
if usdpath.exists() and thumbnailpath.exists():
    add_asset(assetname, usdpath, thumbnailpath)

for usd in folder.glob("*.usd"):
    assetname = usd.stem
    thumbnailpath = folder/"thumbnails"/(assetname + "_thumbnail.png")
    if thumbnailpath.exists():
        add_asset(assetname, str(usd), thumbnailpath)
