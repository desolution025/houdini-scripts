##### THIS SCRIPT CONVERT THE CONTENT OF A PRINCIPLED SHADER TEXTURES TO A MATERIALX NETWORK (+ USD PREVIEW OPTIONAL)#############
##### LATEST UPDATE  09/07/22 - v002
### BY ADRIEN LAMBERT
### GUMROAD.COM/ADRIENLAMBERT


import hou

mysel = hou.selectedNodes()[0]

matcontext = mysel.parent()


preview = hou.ui.displayMessage(text="You are about to convert to materialX, Do you want to create an USD preview shader as well ?", buttons=["MaterialX Only", "+ CREATE PREVIEW", "CANCEL"])

if preview == 1 or preview ==0:
    matsubnet = matcontext.createNode("subnet", mysel.name() + "_mtlX")


    ## DEFINE OUTPUT SURFACE
    surfaceoutput = matsubnet.createNode("subnetconnector", "surface_output")
    surfaceoutput.parm("parmname").set("surface")
    surfaceoutput.parm("parmlabel").set("Surface")
    surfaceoutput.parm("parmtype").set("surface")
    surfaceoutput.parm("connectorkind").set("output")
    
    
    ## DEFINE OUTPUT DISPLACEMENT
    dispoutput = matsubnet.createNode("subnetconnector", "displacement_output")
    dispoutput.parm("parmname").set("displacement")
    dispoutput.parm("parmlabel").set("Displacement")
    dispoutput.parm("parmtype").set("displacement")
    dispoutput.parm("connectorkind").set("output")
    
    #CREATE MATERIALX STANDARD
    mtlx =  matsubnet.createNode("mtlxstandard_surface", "surface_mtlx")
    surfaceoutput.setInput(0, mtlx)
    
    #CREATE ALBEDO
    path = mysel.parm("basecolor_texture").eval()
    albedopath = path
    albedo = matsubnet.createNode("mtlximage", "ALBEDO")
    albedo.parm("file").set(path)
    mtlx.setInput(1, albedo)
    
    #CREATE ROUGHNESS
    path = mysel.parm("rough_texture").eval()
    roughpath = path
    rough = matsubnet.createNode("mtlximage", "ROUGHNESS")
    rough.parm("file").set(path)
    rough.parm("signature").set("0")
    mtlx.setInput(6, rough)
    
    #CREATE SPECULAR
    if mysel.parm("reflect_useTexture").eval() == 1:
        path = mysel.parm("reflect_texture").eval()
        spec= matsubnet.createNode("mtlximage", "REFLECT")
        spec.parm("file").set(path)
        mtlx.setInput(5, spec)
    
    #CREATE OPACITY IF NEEDED
    if mysel.parm("opaccolor_useTexture").eval() == 1:
        path = mysel.parm("opaccolor_texture").eval()
        opac = matsubnet.createNode("mtlximage", "OPACITY")
        opac.parm("file").set(path)
        mtlx.setInput(38, opac)
    
    
    
        
    #CREATE NORMAL
    if mysel.parm("baseBumpAndNormal_enable").eval() == 1:
        path = mysel.parm("baseNormal_texture").eval()
        normal = matsubnet.createNode("mtlximage", "NORMAL")
        normal.parm("signature").set("vector3")
        plugnormal = matsubnet.createNode("mtlxnormalmap" )
        normal.parm("file").set(path)
        mtlx.setInput(40, plugnormal)
        plugnormal.setInput(0, normal)
        
        
    #CREATE DISPLACEMENT
    if mysel.parm("dispTex_enable").eval() == 1:
        # GETTING THE PARAMETERS VALUE
        path = mysel.parm("dispTex_texture").eval()
        offset= mysel.parm("dispTex_offset").eval()
        scale= mysel.parm("dispTex_scale").eval()
        #CREATING DISPLACE NODES
        displace = matsubnet.createNode("mtlximage", "DISPLACE")
        plugdisplace = matsubnet.createNode("mtlxdisplacement" )
        remapdisplace = matsubnet.createNode("mtlxremap", "OFFSET_DISPLACE" )
        #SETTING PARAMETERS DISPLACE
        #set remap
        remapdisplace.parm("outlow").set(offset)
        remapdisplace.parm("outhigh").set(1+offset)
        #set scale displace
        plugdisplace.parm("scale").set(scale)
        #set image displace
        displace.parm("file").set(path)
        displace.parm("signature").set("0")
        
        #SETTING INPUTS
        dispoutput.setInput(0, plugdisplace)
        plugdisplace.setInput(0, remapdisplace)
        remapdisplace.setInput(0, displace)
        
    matcontext.layoutChildren()
    
    #set Component material if in scene
    compmat = matcontext.outputs()[0]
    if compmat.type().description() == "Component Material" :
        compmat.parm("matspecpath1").set("/ASSET/mtl/" +  matsubnet.name())
        
if preview == 1:
    
    usdpreview = matcontext.createNode("usdpreviewsurface", mysel.name() + "_preview")
    usdtexture = matcontext.createNode("usduvtexture::2.0", "albedo_usduvtexture")
    usdtexturerough = matcontext.createNode("usduvtexture::2.0", "roughness_usduvtexture")
    primvar = matcontext.createNode("usdprimvarreader", "usdPrimvarReader")
    usdpreview.parm("useSpecularWorkflow").set(1)
    
    primvar.parm("signature").set("float2")
    primvar.parm("varname").set("st")
    
    usdtexture.parm("file").set(albedopath)
    usdtexture.parm("sourceColorSpace").set("sRGB")
    
    usdtexturerough.parm("file").set(roughpath)
    usdtexturerough.parm("sourceColorSpace").set("raw")
    
    usdtexture.setInput(1, primvar)
    usdtexturerough.setInput(1, primvar)
    usdpreview.setInput(0, usdtexture,4)
    usdpreview.setInput(5, usdtexturerough,0)
    
    #CREATE SPEC IF NEEDED
    if mysel.parm("reflect_useTexture").eval() == 1:
        path = mysel.parm("reflect_texture").eval()
        specpreview= matcontext.createNode("usduvtexture::2.0", "spec_usduvtexture")
        specpreview.parm("file").set(path)
        usdpreview.setInput(3, specpreview,4)
        specpreview.parm("sourceColorSpace").set("raw")
        specpreview.setInput(1, primvar)
    #CREATE OPACITY IF NEEDED
    if mysel.parm("opaccolor_useTexture").eval() == 1:
        path = mysel.parm("opaccolor_texture").eval()
        opacpreview = matcontext.createNode("usduvtexture::2.0", "opacity_usduvtexture")
        opacpreview.parm("file").set(path)
        usdpreview.setInput(8, opacpreview,0)
        opacpreview.setInput(1, primvar)
        opacpreview.parm("sourceColorSpace").set("raw")
        usdpreview.parm("opacityThreshold").set(0.05)
    
    test = matcontext.outputs()[0]
    if test.type().description() == "Component Material" :
        edit = test.node("edit")
        assign = edit.createNode("assignmaterial")
        assign.parm("matspecpath1").set("/ASSET/mtl/" +  mysel.name() + "_preview")
        output = edit.node("output0")
        subinputs = edit.indirectInputs()  

        output.setInput(0, assign)
        assign.setInput(0,subinputs[0])
        edit.layoutChildren()
        
        purpose = assign.parm("bindpurpose1")
        purpose.set(purpose.menuItems()[-1])
        
    matcontext.layoutChildren()
    selpos = mysel.position()
    pos = selpos[0]+1, selpos[1]-2
    mysel.setPosition(pos)

    matsubnetpos = matsubnet.position()
    pos = matsubnetpos[0]-2, matsubnetpos[1]-2
    matsubnet.setPosition(pos)
    
    


matsubnet.layoutChildren()
