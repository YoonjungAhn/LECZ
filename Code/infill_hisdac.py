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
arcpy.env.workspace = r"F:\lecz\sample_processing\blocks"  # Update with your workspace path
fcs=arcpy.ListFeatureClasses("*block*")
for input_fc in fcs:
    print(f"Processing {input_fc}")
    inmem_fc = r'in_memory'+os.sep+os.path.basename(input_fc)[:-4]
    arcpy.CopyFeatures_management(input_fc,inmem_fc)
    # Create a layer from the feature class
    layer_name = os.path.basename(input_fc)[:-4]
    arcpy.MakeFeatureLayer_management(inmem_fc, layer_name)
    # Add the BUAINFILL field if it doesn't already exist
    field_name = "INFILL"    
    arcpy.AddField_management(layer_name, field_name, "SHORT")
    arcpy.CalculateField_management(layer_name, field_name, "0", "PYTHON3")
    print(f"Field {field_name} added.")
    print(f"Default value of {field_name} set to 0.")
    
    # Select features where HISDAC_DEV_TOTAL < 1 AND NLCD_DEV_TOTAL > 0
    selection_query = '"BUATOT_DV" < 1 AND "NTOT_DV" > 0'
    arcpy.SelectLayerByAttribute_management(layer_name, "NEW_SELECTION", selection_query)
    print(f"Selected features with query: {selection_query}")
    # update calculations
    arcpy.CalculateField_management(layer_name, field_name, "1", "PYTHON3")
    for hisdacProp in propList:
        nProp=hisdacProp.replace("BUA","N")
        arcpy.CalculateField_management(layer_name, hisdacProp, "!"+nProp+"!", "PYTHON3")
    for hisdacPop in popList:
        nPop=hisdacPop.replace("HPOP","NPOP")
        arcpy.CalculateField_management(layer_name, hisdacPop, "!"+nPop+"!", "PYTHON3")
    final_fc = r"F:\lecz\sample_processing\merge\blocks.gdb"+os.sep+os.path.basename(input_fc)[:-4]
    arcpy.CopyFeatures_management(inmem_fc,final_fc)
    print("Selection and calculations completed successfully!")
