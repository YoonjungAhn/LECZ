import arcpy, os
arcpy.env.overwriteOutput=True
zstatDir=r'F:\lecz\zonal_stats_global_data_v3'
countyDir = r'F:\lecz\sample_processing\merge'

arcpy.env.workspace=countyDir

fcs=arcpy.ListFeatureClasses("county*0.shp")

for fc in fcs:
    print("Processing "+fc[7:11])
    masterDict={}
    year=fc[7:11]
    fc=countyDir+os.sep+fc
    # change dir to zstatDir and read all of the values
    arcpy.env.workspace=zstatDir
    tbls=arcpy.ListTables("*"+year+"*")
    for tbl in tbls:
        valueDict={}
        # print(tbl)
        if "gpw411" in tbl:
            ds="GPWPOP_"
            if "gpw411_unadj" in tbl:
                ds="GPWUN_"
            if "landarea" in tbl:
                ds="GPWLA_"
        elif "ghspop" in tbl:
            ds="GHSPOP_"
        elif "landscan" in tbl:
            ds="LSCPOP_"
        elif "worldpop" in tbl:
            ds="WPPOP_"
        if "0_10" in tbl:
            cat="IN"
        elif "out_of" in tbl:
            cat="OUT"
        else:
            cat="TOT"
        field=ds+cat
        # print(field)
        with arcpy.da.SearchCursor(tbl,["FIPSSTCO","SUM"]) as rows:
            for row in rows:
                valueDict[row[0]]=row[1]
        masterDict[field]=valueDict
    # copy the fields to the fc
    inMemFC="in_memory"+os.sep+os.path.basename(fc)[:-4]
    arcpy.CopyFeatures_management(fc,inMemFC)
    # print(masterDict.keys())
    newFields=sorted(list(masterDict.keys()))
    for newField in newFields:
        print(newField)
        arcpy.AddField_management(inMemFC,newField,"DOUBLE")
    with arcpy.da.UpdateCursor(inMemFC,["FIPSSTCO"]+newFields) as cursor:
        for row in cursor:
            key=row[0]
            if year=="1990" or year=="2000" or year=="2020":
                try:
                    row[1]=masterDict["GHSPOP_IN"][key]
                except:
                    row[1]=0
                try:
                    row[2]=masterDict["GHSPOP_OUT"][key]
                except:
                    row[2]=0
                try:
                    row[3]=masterDict["GHSPOP_TOT"][key]
                except:
                    row[3]=0
                try:
                    row[4]=masterDict["GPWPOP_IN"][key]
                except:
                    row[4]=0
                try:
                    row[5]=masterDict["GPWPOP_OUT"][key]
                except:
                    row[5]=0
                try:
                    row[6]=masterDict["GPWPOP_TOT"][key]
                except:
                    row[6]=0
                try:
                    row[7]=masterDict["GPWUN_IN"][key]
                except:
                    row[7]=0
                try:
                    row[8]=masterDict["GPWUN_OUT"][key]
                except:
                    row[8]=0
                try:
                    row[9]=masterDict["GPWUN_TOT"][key]
                except:
                    row[9]=0
                if year=="2000" or year=="2020":
                    try:
                        row[10]=masterDict["LSCPOP_IN"][key]
                    except:
                        row[10]=0
                    try:
                        row[11]=masterDict["LSCPOP_OUT"][key]
                    except:
                        row[11]=0
                    try:
                        row[12]=masterDict["LSCPOP_TOT"][key]
                    except:
                        row[12]=0
                    try:
                        row[13]=masterDict["WPPOP_IN"][key]
                    except:
                        row[13]=0
                    try:
                        row[14]=masterDict["WPPOP_OUT"][key]
                    except:
                        row[14]=0
                    try:
                        row[15]=masterDict["WPPOP_TOT"][key]
                    except:
                        row[15]=0
            else:
                try:
                    row[1]=masterDict["GHSPOP_IN"][key]
                except:
                    row[1]=0
                try:
                    row[2]=masterDict["GHSPOP_OUT"][key]
                except:
                    row[2]=0
                try:
                    row[3]=masterDict["GHSPOP_TOT"][key]
                except:
                    row[3]=0
                try:
                    row[4]=masterDict["GPWLA_IN"][key]
                except:
                    row[4]=0
                try:
                    row[5]=masterDict["GPWLA_OUT"][key]
                except:
                    row[5]=0
                try:
                    row[6]=masterDict["GPWLA_TOT"][key]
                except:
                    row[6]=0
                try:
                    row[7]=masterDict["GPWPOP_IN"][key]
                except:
                    row[7]=0
                try:
                    row[8]=masterDict["GPWPOP_OUT"][key]
                except:
                    row[8]=0
                try:
                    row[9]=masterDict["GPWPOP_TOT"][key]
                except:
                    row[9]=0
                try:
                    row[10]=masterDict["GPWUN_IN"][key]
                except:
                    row[10]=0
                try:
                    row[11]=masterDict["GPWUN_OUT"][key]
                except:
                    row[11]=0
                try:
                    row[12]=masterDict["GPWUN_TOT"][key]
                except:
                    row[12]=0                
                try:
                    row[13]=masterDict["LSCPOP_IN"][key]
                except:
                    row[13]=0
                try:
                    row[14]=masterDict["LSCPOP_OUT"][key]
                except:
                    row[14]=0
                try:
                    row[15]=masterDict["LSCPOP_TOT"][key]
                except:
                    row[15]=0
                try:
                    row[16]=masterDict["WPPOP_IN"][key]
                except:
                    row[16]=0
                try:
                    row[17]=masterDict["WPPOP_OUT"][key]
                except:
                    row[17]=0
                try:
                    row[18]=masterDict["WPPOP_TOT"][key]
                except:
                    row[18]=0
            # print(row)
            cursor.updateRow(row)
    # copy the fields to the fc
    outFC=r"F:\lecz\sample_processing\final_county"+os.sep+os.path.basename(fc)
    arcpy.CopyFeatures_management(inMemFC,outFC)
    print("Created "+outFC)