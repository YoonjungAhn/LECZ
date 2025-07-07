import arcpy, os

finalFile=r'F:\lecz\sample_processing\final_county_data.gdb\county_2020_with_time_series_attributes'
countyDir = r"F:\lecz\sample_processing\final_county"
arcpy.env.workspace=countyDir
fcs=arcpy.ListFeatureClasses("*")
masterNewFields=[]
masterSortedNewFields=[]
masterValueDict={}
for fc in fcs:
    print("Processing "+fc[7:11])    
    year=fc[7:11]
    # read fields
    fields=arcpy.ListFields(fc,"*")
    newFields=[]
    lookupFields=["FIPSSTCO"]
    for field in fields:
        fieldName=field.name
        if fieldName=="FID" or fieldName=="Shape" or fieldName=="FIPSSTCO":
            continue
        lookupFields.append(fieldName)
        if fieldName=="NTOT_DV":
            fieldName="NLCDAREA_TOT_DV"
        if fieldName=="NIN_DV":
            fieldName="NLCDAREA_IN_DV"
        if fieldName=="NOUT_DV":
            fieldName="NLCDAREA_OUT_DV"
        if "CPOP" in fieldName:
            if not "LSC" in fieldName:
                fieldName=fieldName.replace("CPOP","CENSUSPOP")
            else:
                fieldName=fieldName.replace("LSC","LANDSCAN") 
        if "HPOP" in fieldName:
            fieldName=fieldName.replace("HPOP","HISDACPOP")
        if "NPOP" in fieldName:
            if not "LANDSCAN" in fieldName:
                fieldName=fieldName.replace("NPOP","NLCDPOP")
        if "BUATOT" in fieldName:
            fieldName="HISDACAREA_TOT"
        if "BUAIN" in fieldName:
            fieldName="HISDACAREA_IN"
        if "BUAOUT" in fieldName:
            fieldName="HISDACAREA_OUT"
        if "WP" in fieldName:
            if not "GPW" in fieldName:
                fieldName=fieldName.replace("WP","WORLD")
        newFields.append(fieldName+"_"+year)
    # print(lookupFields)
    sortedNewFields=sorted(newFields)
    masterSortedNewFields=masterSortedNewFields+sortedNewFields
    # print("Created "+outFC)
    # assemble the dictionary
    valueDict={}
    with arcpy.da.SearchCursor(fc,lookupFields) as rows:
        for row in rows:
            row_dict = dict(zip(["FIPSSTCO"]+newFields, row))
            valueDict[row[0]]=row_dict
    masterValueDict[year]=valueDict 
# print(list(masterValueDict.keys()))
dict90=masterValueDict[list(masterValueDict.keys())[0]]
dict00=masterValueDict[list(masterValueDict.keys())[1]]
dict10=masterValueDict[list(masterValueDict.keys())[2]]
dict20=masterValueDict[list(masterValueDict.keys())[3]]

# Create a dictionary mapping field names to their indices
field_indices = {field: index for index, field in enumerate(["FIPSSTCO"]+masterSortedNewFields)}
# print(field_indices)
# print(dict90['01003'])   
# print(dict00['01003']) 
# print(dict10['01003']) 
# print(dict20['01003'])      
# add fields to finalFile
for fld in masterSortedNewFields:
    arcpy.AddField_management(finalFile,fld,"DOUBLE") 
# now update them
with arcpy.da.UpdateCursor(finalFile,["FIPSSTCO"]+masterSortedNewFields) as cursor:
    for row in cursor:
        key=row[0]
        for k,v in field_indices.items():
            if k == 'FIPSSTCO':
                continue
            if "1990" in k:
                vDict=dict90
            elif "2000" in k:
                vDict=dict00
            elif "2010" in k:
                vDict=dict10
            elif "2020" in k:
                vDict=dict20
            try:
                row[v]=vDict[key][k]
            except:
                print(key + " is missing from " + str(vDict[vDict.keys()[0]]))
                row[v]=0
        cursor.updateRow(row)
