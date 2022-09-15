from collections import defaultdict
from os import PathLike
from typing import List, Tuple, Sequence, Mapping, Optional
import re
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path
try:
    import ujson as json
except ImportError:
    import json
from loguru import logger


DIFFUSE = ("diffuse", "albedo", "color", "basecolor", "diff")
SPECULAR = ("specular", "spec")
ROUGHNESS = ("roughness",)
GLOSSINESS = ("glossiness",)
NORMAL = ("normal", "nrm")
BUMP = ("bump", "bmp")
HEIGHT = ("height",)
DISPLACEMENT = ("displacement", "disp")
OPACITY = ("opacity", "opac")
TRANSLUCENCY = ("translucency",)
TRANSMISSION = ("transmission",)

TEXSUFFIX = ('exr','png', 'jpg', 'jpeg')



class PBR_Tex_Folder:

    channels_mapping = {
                    "Diffuse": ["diffuse", "albedo", "basecolor", "color", "diff"],
                    "Specular": ["specular", "spec"],
                    "Metalness": ["metalness", "metallic"],
                    "Roughness": ["roughness", "rough"],
                    "Glossiness": ["glossiness", "gloss"],
                    "IOR": ["ior"],
                    "Normal": ["normal", "nrm"],
                    "Bump": ["bump", "bmp"],
                    "Height": ["height",],
                    "Displacement": ["displacement", "disp"],
                    "Opacity": ["opacity", "opac"],
                    "Translucency": ["translucency"],
                    "Transmission": ["transmission"],
                    "Emission": ["emission"]
                }
    tex_suffix = ['exr','png', 'jpg', 'jpeg']

    def __init__(self, path: PathLike,
                channels: Sequence[str]=[
                    "Diffuse",
                    "Specular", 
                    "Metalness",
                    "Roughness",
                    "Glossiness",
                    "Normal",
                    "Displacement",
                    "Opacity",
                    "Translucency",
                    "Transmission",
                    "Emission"
                ],
                texsuffix: Sequence[str]=['exr','png', 'jpg', 'jpeg'],
                *,
                mtlprefix: Optional[str]=None,
                subfolder: Optional[PathLike]=None) -> None:
        self.path, self.channels, self.texsuffix, self.mtlprefix, self.subfolder = Path(path), channels, texsuffix, mtlprefix, subfolder
        self.not_matched = None  # A list for files not matched

    def all_tex(self) -> List[PathLike]:
        texs = []
        for suf in TEXSUFFIX:
            texs.extend(self.path.glob(f'*.{suf}'))
        logger.debug(f'ALL texures in folder: {list(map(lambda x: x.name, texs))}')
        return texs

    def parse_channel(self, channel: str) -> Optional[Tuple[Mapping[str, PathLike], Mapping[str, List[PathLike]]]]:
        texs = {}
        repeated_files = defaultdict(list)
        if self.not_matched is None:
            self.not_matched = self.all_tex()

        type_feature = "|".join(self.__class__.channels_mapping[channel])
        suffix_feature = "|".join(self.texsuffix)
        repattern = rf"(.*?)({type_feature}).*?\.({suffix_feature})"
        logger.debug(f"Filter files with rule: {repattern}")

        for f in self.not_matched:
            match = re.match(repattern, f.name, flags=re.I)

            if match:
                prefix_ = match.group(1).rstrip('_')
                if prefix_ in texs:
                    logger.info(f"There is already matched a {channel} texture for material {prefix_}, ignore file: {f.name}")
                    repeated_files[f"{match.group(1)}{channel}"].append(str(f))
                    continue
                texs[prefix_] = f
                logger.debug(f"Matched file: {f}")

        if texs:
            for f in texs.values():
                self.not_matched.remove(f)  # Remove files that has matched
            return texs, repeated_files

        if not texs:  # No file match
            logger.info(f"Did not found file matching rule of channel {channel}")

    def makeup_mtl(self):
        mtls = defaultdict(dict)
        varians = defaultdict(dict)
        for c in self.channels:
            result = self.parse_channel(c)
            if result is not None:
                texs, repeated_files = result
                for m, t in texs.items():
                    mtls[m][c] = t
                for m ,l in repeated_files.items():
                    varians[m][c] = l
        return mtls, varians



if __name__ == "__main__":
    folder1 = r"F:\3D Models\Model Pack\KitBash3D\KitBash3D - Mini Kit Aristocracy\KB3DTextures"
    folder2 = r"F:\Footage\Magascan Libary\Downloaded\3d\3d_assembly_uhqibgfga"

    pmf = PBR_Tex_Folder(folder1)
    dd, va = pmf.makeup_mtl()
    print(dd)