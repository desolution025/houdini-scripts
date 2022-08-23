from connect_houdini import *


def set_volume_size(node):
    pyrosrc = node
    while True:
        pyrosrc = pyrosrc.inputs()[0]
        if pyrosrc.type().name() == 'pyrosource':
            break
        # pyrosrc = input
    sep = pyrosrc.parm('particlesep').name()
    scale = pyrosrc.parm('particlescale').name()
    node.parm('voxelsize').setExpression("ch('../{pysrc}/{sep}') * ch('../{pysrc}/{scale}') * 0.25".format(pysrc=pyrosrc, sep=sep, scale=scale))


def main():
    nodes = hou.selectedNodes()
    for node in nodes:
        if node.type().name() != 'volumerasterizeattributes':
            continue
        set_volume_size(node)


if __name__ =="__main__":
    main()