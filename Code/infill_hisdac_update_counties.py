import arcpy,os

# need to make selections and calculations
# if hisdac dev total <1 AND nlcd dev total > 0
# add field to mark as 0 or 1 to indicate which items are infilled BUAINFILL
# for infilled items make the following field calculations
# BUATOT_DV = NTOT_DV

propList=["BUATOT_DV","BUAIN_DV","BUAOUT_DV","BUATOT_UD","BUAIN_UD","BUAOUT_UD",
 "BUAPTOT_DV","BUAPIN_DV","BUAPOUT_DV","BUAPTOT_UD","BUAPIN_UD","BUAPOUT_UD"]

popList=["HPOP_TOT","HPOP_IN","HPOP_OUT"]

# Set the workspace and input feature class
arcpy.env.workspace = r"F:\lecz\sample_processing\merge\blocks.gdb"  # Update with your workspace path
yearList=["2010"]#["1990","2000","2010","2020"]
for year in yearList:
    blockDict={}
    fcs=arcpy.ListFeatureClasses("*"+year+"*")
    for fc in fcs:
        print(f"processing {fc}")        
        countyFile=r'F:\lecz\sample_processing\final_county'+os.sep+"county_"+str(year)+".shp"
        # update HPOP_TOT, HPOP_IN, HPOP_OUT        
        with arcpy.da.SearchCursor(fc,["FIPSSTCO","BUATOT_DV","BUAIN_DV","BUAOUT_DV","HPOP_TOT", "HPOP_IN", "HPOP_OUT","INFILL"]) as rows:
            for row in rows:
                key=row[0]
                buatot=row[1]
                buain=row[2]
                buaout=row[3]
                hpoptot=row[4]
                hpopin=row[5]
                hpopout=row[6]
                infill=row[7]
                if key not in blockDict.keys():
                    infillCount=1
                    blockDict[key]=[buatot,buain,buaout,hpoptot,hpopin,hpopout,infill,infillCount]

                else:                    
                    blockDict[key]=[blockDict[key][0]+buatot,blockDict[key][1]+buain,blockDict[key][2]+buaout,
                                    blockDict[key][3]+hpoptot,blockDict[key][4]+hpopin,blockDict[key][5]+hpopout,blockDict[key][6]+infill,blockDict[key][7]+infillCount]
    print("Created block value dictionary")
    arcpy.AddField_management(countyFile,"INFILL","SHORT")
    arcpy.AddField_management(countyFile,"INFILLP","DOUBLE")
    arcpy.AddField_management(countyFile,"TOTBLOCKS","SHORT")
    with arcpy.da.UpdateCursor(countyFile,["FIPSSTCO","BUATOT_DV","BUAIN_DV","BUAOUT_DV","HPOP_TOT", "HPOP_IN", "HPOP_OUT","INFILL","INFILLP","TOTBLOCKS"]) as cursor: 
        for row in cursor:
            key=row[0]
            row[1]=blockDict[key][0]
            row[2]=blockDict[key][1]
            row[3]=blockDict[key][2]
            row[4]=blockDict[key][3]
            row[5]=blockDict[key][4]
            row[6]=blockDict[key][5]
            row[7]=blockDict[key][6]
            row[9]=blockDict[key][7]
            try:
                row[8]=blockDict[key][6]/blockDict[key][7]
            except: 
                row[8]=0
            try:
                cursor.updateRow(row)
            except:
                print(row)
    print("Transferred Attributes")