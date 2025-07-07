import arcpy,os
arcpy.CheckOutExtension("SPATIAL")
arcpy.env.overwriteOutput=True
workspace=r'F:\lecz\sample_processing\merge'
leczInClip=r'F:\lecz\elevation\usa1_merit_0_10_lecz.shp'
leczOutClip=r'F:\lecz\elevation\usa1_merit_out_of_lecz.shp'
outRasterFolder=r'F:\lecz\sample_processing\merge_raster'
mollweideFile = r'F:\lecz\values_global_data\mollweide\usa1_ghspop_1990.tif'
mollweidePrj = arcpy.Describe(mollweideFile).spatialReference.exportToString()
arcpy.env.workspace=workspace
fcs=arcpy.ListFeatureClasses("*0.shp")
for fc in fcs:
    try:
        if "block" in fc:
            joinField="GISJOIN"
        else:
            joinField="FIPSSTCO"
        print("Processing " + fc)
        prjList=[fc]
        clipInFC=os.path.join(workspace,fc.replace(".shp","_merit_0_10_lecz.shp"))
        if not arcpy.Exists(clipInFC):
            arcpy.Clip_analysis(fc,leczInClip,clipInFC)
            print("Clipped " + clipInFC)
        prjList.append(clipInFC)
        clipOutFC=os.path.join(workspace,fc.replace(".shp","_merit_out_of_lecz.shp"))
        if not arcpy.Exists(clipOutFC):
            arcpy.Clip_analysis(fc,leczOutClip,clipOutFC)
            print("Clipped " + clipOutFC)
        prjList.append(clipOutFC)
        for prjIn in prjList:
            prjOut=os.path.join(workspace+"_mollweide",os.path.basename(prjIn).replace(".shp","_mollweide.shp"))
            if not arcpy.Exists(prjOut):
                arcpy.Project_management(prjIn,prjOut,mollweidePrj)
                print("Projected " + prjIn)
            # create rasters from both
            outRaster=os.path.join(outRasterFolder,os.path.basename(prjIn).replace(".shp",".tif"))
            if not arcpy.Exists(outRaster):
                arcpy.env.cellSize=0.000833
                arcpy.env.extent=arcpy.Extent(-125.0, 24.0, -66.0, 55.0)
                arcpy.PolygonToRaster_conversion(prjIn,joinField,outRaster,"CELL_CENTER")
                print("Created " + outRaster)
            outPrjRaster=os.path.join(outRasterFolder,os.path.basename(prjOut).replace(".shp",".tif"))
            if not arcpy.Exists(outPrjRaster):
                arcpy.env.cellSize=100
                arcpy.env.extent=arcpy.Extent(-11846547.112704, 2933971.956211, -5020147.112704, 5873471.956211)
                arcpy.PolygonToRaster_conversion(prjOut,joinField,outPrjRaster,"CELL_CENTER")
                print("Created " + outPrjRaster)
    except:
        print(arcpy.GetMessages())