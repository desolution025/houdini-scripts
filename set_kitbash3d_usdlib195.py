from os import PathLike
from pathlib2 import Path
try:
    from connect_houdini import hou
except ImportError:
    import hou
from loguru import logger


def add_asset(db : hou.AssetGalleryDataSource, name: str, path: PathLike, thumbnail_path: PathLike):
    # read in the thumbnail
    thumbnail = Path(thumbnail_path).read_bytes()

    # add the database entry
    item_uuid = db.addItem(
        name,
        str(path),
        thumbnail)
    logger.success(f'insert a new asset uuid: {item_uuid}')

def batch_addItem(folder: PathLike):
    # assert_db: hou.AssetGalleryDataSource):
    usd_folder = Path(hou.expandString(folder))
    logger.debug(f"Choosed the usd folder: {usd_folder}")

    assert_db = hou.ui.sharedLayoutDataSource()

    thumbnailfolder = usd_folder.glob("thumbnails")
    if thumbnailfolder:
        thumbnailfolder = list(thumbnailfolder)[0]
        logger.debug(f"Thumbnails folder {thumbnailfolder}")
        for usd in usd_folder.glob("*"):
            if usd.is_dir() and not usd.samefile(thumbnailfolder):
                add_asset(assert_db, str(usd.name), str(usd/(str(usd.name) + ".usd")), thumbnailfolder/(str(usd.name) + ".png"))
    else:
        logger.warning("Did not found thumbnails folder")
    
    #Refresh Asset Gallery
    hou.ui.reloadSharedLayoutDataSource()

if __name__ == "__main__":
    folder : PathLike = hou.ui._selectFile(title="Choose USD Directory", file_type=hou.fileType.Directory, chooser_mode=hou.fileChooserMode.Read)
    batch_addItem(folder)