# Import modules
import datetime
scriptTime=datetime.datetime.now()
import os
import sys
import traceback
import shutil
import arcpy
import multiprocessing 

# Enable spatial analyst extension
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput=True

# Set base directories and hardcoded input files
clipFCIn=r'F:\lecz\elevation\usa1_merit_0_10_lecz.shp'
clipFCOut=r'F:\lecz\elevation\usa1_merit_out_of_lecz.shp'
base_path = r"F:\lecz\sample_processing"
nlcd_base_path = r"F:\lecz\nlcd"
hisdac_base_path =  r'F:\lecz\hisdac\BUA'
output_dirs = {
    "prj": os.path.join(base_path, "blocks_albers"),
    "buffer": os.path.join(base_path, "blocks_albers_buffers"),
    "raster": os.path.join(base_path, "blocks_albers_rasters"),
    "raster_nlcd": os.path.join(base_path, "blocks_albers_rasters_nlcd"),
    "vector_nlcd": os.path.join(base_path, "blocks_albers_nlcd"),
    "intersect": os.path.join(base_path, "blocks_albers_intersect.gdb"),
    "dissolve": os.path.join(base_path, "blocks_albers_dissolve"),
    "clip_in": os.path.join(base_path, "clip_0_10m"),
    "clip_out": os.path.join(base_path, "clip_out_of_lecz"),
    "scratch": os.path.join(base_path, "scratch"),
    "county": os.path.join(base_path, "county")
}

# functions
def calculate_uniform_proportions(fc):
    try:
        # clip by lecz and calculate land area as in clip_blocks.py
        # Clean pre-existing and add new fields
        arcpy.DeleteField_management(fc,"AREA_GEO") 
        arcpy.DeleteField_management(fc,"AREA_IN")        
        arcpy.DeleteField_management(fc,"AREA_OUT")
        # calculate total area in fc
        #arcpy.CalculateGeometryAttributes_management(fc,"AREA_TOT AREA_GEODESIC",'#',"SQUARE_METERS")
        # arcpy.CalculateField_management(fc,"AREA_TOT","!shape.getArea('GEODESIC', 'SQUAREMETERS')!","PYTHON")
        arcpy.AddField_management(fc,"AREA_TOT","DOUBLE")
        with arcpy.da.UpdateCursor(fc, ["SHAPE@", "AREA_TOT"]) as cursor: 
            for row in cursor:
                row[1] = row[0].getArea('GEODESIC', 'SquareMeters')
                cursor.updateRow(row)
        # clip to inside and outside lecz        
        inFC=os.path.join(output_dirs["clip_in"],os.path.basename(fc))
        outFC=os.path.join(output_dirs["clip_out"],os.path.basename(fc))
        arcpy.Clip_analysis(fc,clipFCIn,inFC)
        arcpy.Clip_analysis(fc,clipFCOut,outFC)
        # arcpy.CalculateGeometryAttributes_management(inFC,"AREA_IN AREA_GEODESIC",'#',"SQUARE_METERS")
        # arcpy.CalculateField_management(inFC,"AREA_IN","!shape.getArea('GEODESIC', 'SQUAREMETERS')!","PYTHON")
        arcpy.AddField_management(inFC,"AREA_IN","DOUBLE")
        with arcpy.da.UpdateCursor(inFC, ["SHAPE@", "AREA_IN"]) as cursor: 
            for row in cursor:
                row[1] = row[0].getArea('GEODESIC', 'SquareMeters')
                cursor.updateRow(row)
        # arcpy.CalculateGeometryAttributes_management(outFC,"AREA_OUT AREA_GEODESIC",'#',"SQUARE_METERS")
        # arcpy.CalculateField_management(outFC,"AREA_OUT","!shape.getArea('GEODESIC', 'SQUAREMETERS')!","PYTHON")
        arcpy.AddField_management(outFC,"AREA_OUT","DOUBLE")
        with arcpy.da.UpdateCursor(outFC, ["SHAPE@", "AREA_OUT"]) as cursor: 
            for row in cursor:
                row[1] = row[0].getArea('GEODESIC', 'SquareMeters')
                cursor.updateRow(row)
        # these are proportions and proportional land areas in sq meters 
        # of each block inside or outside of the 10m LECZ
        # Populate dictionaries with area values
        with arcpy.da.SearchCursor(inFC, ["GISJOIN", "AREA_IN"]) as rows:
            in_dict = {row[0]: row[1] for row in rows}    
        with arcpy.da.SearchCursor(outFC, ["GISJOIN", "AREA_OUT"]) as rows:
            out_dict = {row[0]: row[1] for row in rows}
        # Clean pre-existing and add new fields
        arcpy.DeleteField_management(fc,"PROP_IN")
        arcpy.DeleteField_management(fc,"PROP_OUT")
        arcpy.AddField_management(fc,"AREA_IN","DOUBLE")        
        arcpy.AddField_management(fc,"AREA_OUT","DOUBLE")
        arcpy.AddField_management(fc,"PROP_IN","DOUBLE")
        arcpy.AddField_management(fc,"PROP_OUT","DOUBLE")
        # Update rows with calculated values
        with arcpy.da.UpdateCursor(fc, ["GISJOIN", "AREA_TOT", "AREA_IN", 
                                        "AREA_OUT", "PROP_IN", "PROP_OUT"]) as cursor:
            for row in cursor:
                gisjoin = row[0]
                total_area = row[1]
                # Retrieve area values from dictionaries or default to 0
                area_in = in_dict.get(gisjoin, 0)
                area_out = out_dict.get(gisjoin, 0)
                # Calculate proportions
                prop_in = float(area_in) / total_area if total_area else 0
                prop_out = float(area_out) / total_area if total_area else 0
                # Adjust proportions if their sum does not equal 1
                prop_sum = prop_in + prop_out
                if prop_sum == 0:  # Both proportions are zero
                    prop_in, prop_out = 0, 1
                elif prop_sum != 1:  # Correct slight floating-point inaccuracies
                    adjustment = (1 - prop_sum) / 2
                    prop_in += adjustment
                    prop_out += adjustment
                # Update row values
                row[2] = area_in
                row[3] = area_out
                row[4] = prop_in
                row[5] = prop_out
                cursor.updateRow(row)
        print("Calculated uniform proportions for " + fc)
        return(1,"Calculated uniform proportions for " + fc)
    except:
        print(str(traceback.format_exc()))
        return(0,str(traceback.format_exc()))
        
def geoprocess(fc, dataset_name, area_field_tot, area_field_in, area_field_out):
    try:
        print(f"Geoprocessing {fc} {dataset_name}")        
        # Parse year and set paths
        year = fc.split("_")[-1].replace(".shp", "")
        # Output files
        prj_fc = os.path.join(output_dirs["prj"], dataset_name+"_"+os.path.basename(fc))
        buffer_fc = os.path.join(output_dirs["buffer"], dataset_name+"_"+os.path.basename(fc))
        prj_raster = os.path.join(output_dirs["raster"], dataset_name+"_"+os.path.basename(fc).replace(".shp", ".tif"))
        dataset_raster = os.path.join(output_dirs["raster_nlcd"], dataset_name+"_"+os.path.basename(fc).replace('.shp', '.tif'))
        dataset_fc_albers = os.path.join(output_dirs["vector_nlcd"], dataset_name+f"_albers_{os.path.basename(fc)}")
        dataset_fc = os.path.join(output_dirs["vector_nlcd"], dataset_name+"_"+os.path.basename(fc))
        intersect_fc = os.path.join(output_dirs["intersect"], dataset_name+"_"+os.path.basename(fc)[:-4])
        dissolve_fc = os.path.join(output_dirs["dissolve"], dataset_name+"_"+os.path.basename(fc))
        in_dataset = os.path.join(output_dirs["clip_in"], dataset_name+"_"+os.path.basename(fc))
        out_dataset = os.path.join(output_dirs["clip_out"], dataset_name+"_"+os.path.basename(fc))        
        if dataset_name=="nlcd":
            dataset = os.path.join(nlcd_base_path, f"Annual_NLCD_LndCov_{year}_CU_C1V0.tif")            
        else:
            dataset = os.path.join(hisdac_base_path, f"{year}_BUA.tif")            
        prj = arcpy.Describe(dataset).spatialReference.exportToString()                

        # Set environments
        arcpy.env.cellSize = dataset
        arcpy.env.extent = dataset

        # Project feature class to Albers
        arcpy.Project_management(fc, prj_fc, prj)      

        # Buffer the feature class
        arcpy.Buffer_analysis(prj_fc, buffer_fc, "1000 Meter", "#", "FLAT", "ALL")        

        # Rasterize the buffer
        arcpy.PolygonToRaster_conversion(buffer_fc, "FID", prj_raster)

        # Extract dataset by mask
        if dataset_name == "hisdac":
            hisdacmask = arcpy.sa.Int(arcpy.sa.ExtractByMask(dataset, prj_raster))
            hisdacmask.save(dataset_raster)
        else:
            mask = arcpy.sa.ExtractByMask(dataset, prj_raster)
            mask.save(dataset_raster)       
        
        # Convert dataset raster to polygons
        arcpy.RasterToPolygon_conversion(dataset_raster, dataset_fc_albers, "NO_SIMPLIFY")

        # Project back to WGS84
        arcpy.Project_management(dataset_fc_albers, dataset_fc, arcpy.SpatialReference(4326))

        # Intersect the dataset with the feature class
        arcpy.PairwiseIntersect_analysis([fc, dataset_fc], intersect_fc, "ALL", "#", "INPUT")
        # arcpy.CalculateGeometryAttributes_management(intersect_fc, f"{area_field_tot} AREA_GEODESIC", "#", "SQUARE_METERS")
        # arcpy.CalculateField_management(intersect_fc,area_field_tot,"!shape.getArea('GEODESIC', 'SQUAREMETERS')!","PYTHON")
        arcpy.AddField_management(intersect_fc,area_field_tot,"DOUBLE")
        with arcpy.da.UpdateCursor(intersect_fc, ["SHAPE@", area_field_tot]) as cursor: 
            for row in cursor:
                row[1] = row[0].getArea('GEODESIC', 'SquareMeters')
                cursor.updateRow(row)

        # Dissolve the intersected features
        arcpy.PairwiseDissolve_analysis(intersect_fc, dissolve_fc, ["GISJOIN","gridcode"], [[area_field_tot, "SUM"]], "MULTI_PART")

        # Clip to in and out of LECZ
        arcpy.Clip_analysis(dissolve_fc, clipFCIn, in_dataset)
        # arcpy.CalculateGeometryAttributes_management(in_dataset, f"{area_field_in} AREA_GEODESIC", "#", "SQUARE_METERS")
        # arcpy.CalculateField_management(in_dataset,area_field_in,"!shape.getArea('GEODESIC', 'SQUAREMETERS')!","PYTHON")
        arcpy.AddField_management(in_dataset,area_field_in,"DOUBLE")
        with arcpy.da.UpdateCursor(in_dataset, ["SHAPE@", area_field_in]) as cursor: 
            for row in cursor:
                row[1] = row[0].getArea('GEODESIC', 'SquareMeters')
                cursor.updateRow(row)
        

        arcpy.Clip_analysis(dissolve_fc, clipFCOut, out_dataset)
        # arcpy.CalculateGeometryAttributes_management(out_dataset, f"{area_field_out} AREA_GEODESIC", "#", "SQUARE_METERS")
        # arcpy.CalculateField_management(out_dataset,area_field_out,"!shape.getArea('GEODESIC', 'SQUAREMETERS')!","PYTHON")
        arcpy.AddField_management(out_dataset,area_field_out,"DOUBLE")
        with arcpy.da.UpdateCursor(out_dataset, ["SHAPE@", area_field_out]) as cursor: 
            for row in cursor:
                row[1] = row[0].getArea('GEODESIC', 'SquareMeters')
                cursor.updateRow(row)
        print("Geoprocessed " + fc)
        return(1,"Geoprocessed " + fc)
    except:
        print(str(traceback.format_exc()))
        return(0,str(traceback.format_exc()))
def calculate_and_apply_allocations(fc):
    try:
        def populate_area_dict(feature_class, fields, categories, special_categories=None):        
            area_dict = {}
            key_field, category_field, value_field = fields
            with arcpy.da.SearchCursor(feature_class, [key_field, category_field, value_field]) as cursor:
                for row in cursor:
                    key = str(row[0])
                    category = str(row[1])
                    value = row[2]
                    # Initialize the key in the dictionary if not already present
                    if key not in area_dict:
                        area_dict[key] = {cat: 0 for cat in categories}
                        if special_categories:
                            for special in special_categories:
                                area_dict[key][special] = 0  # Add special categories
                    # Update the value for the specific category
                    if category in area_dict[key]:
                        area_dict[key][category] += value
                    # Update special categories if applicable
                    if special_categories:
                        for special, components in special_categories.items():
                            if category in components:
                                area_dict[key][special] += value
            return area_dict
        def add_fields_to_feature_class(fc, field_types, categories):        
            lookup_fields = ["GISJOIN"]
            # Assemble fields and add them to the feature class
            for category in categories:
                for field_type in field_types:
                    field_name = f"{field_type}{category}"
                    lookup_fields.append(field_name)
                    arcpy.AddField_management(fc, field_name, "DOUBLE")
            return lookup_fields
        def process_nlcd_fields(fc,nlcd_fields,tot_area_nlcd,in_area_nlcd,out_area_nlcd,nlcd_categories):
            with arcpy.da.UpdateCursor(fc,nlcd_fields) as cursor:
                for row in cursor:
                    key=row[0]
                    # grab the totals
                    if key in tot_area_nlcd.keys():
                        tot11=tot_area_nlcd[key]["11"]
                        tot21=tot_area_nlcd[key]["21"]
                        tot22=tot_area_nlcd[key]["22"]
                        tot23=tot_area_nlcd[key]["23"]
                        tot24=tot_area_nlcd[key]["24"]
                        tot31=tot_area_nlcd[key]["31"]
                        tot41=tot_area_nlcd[key]["41"]
                        tot42=tot_area_nlcd[key]["42"]
                        tot43=tot_area_nlcd[key]["43"]
                        tot52=tot_area_nlcd[key]["52"]
                        tot71=tot_area_nlcd[key]["71"]
                        tot81=tot_area_nlcd[key]["81"]
                        tot82=tot_area_nlcd[key]["82"]
                        tot90=tot_area_nlcd[key]["90"]
                        tot95=tot_area_nlcd[key]["95"]
                        totDV=sum([tot21,tot22,tot23,tot24])
                        totUD=sum([tot11,tot31,tot41,tot42,
                                tot43,tot52,tot71,tot81,
                                tot82,tot90,tot95])
                        totSum=sum([tot21,tot22,tot23,tot24,
                                    tot11,tot31,tot41,tot42,
                                    tot43,tot52,tot71,tot81,
                                    tot82,tot90,tot95])
                    else:
                        tot11=0
                        tot21=0
                        tot22=0
                        tot23=0
                        tot24=0
                        tot31=0
                        tot41=0
                        tot42=0
                        tot43=0
                        tot52=0
                        tot71=0
                        tot81=0
                        tot82=0
                        tot90=0
                        tot95=0
                        totDV=0
                        totUD=0
                        totSum=0
                    
                    # grab the in
                    if key in in_area_nlcd.keys():
                        in11=in_area_nlcd[key]["11"]
                        in21=in_area_nlcd[key]["21"]
                        in22=in_area_nlcd[key]["22"]
                        in23=in_area_nlcd[key]["23"]
                        in24=in_area_nlcd[key]["24"]
                        in31=in_area_nlcd[key]["31"]
                        in41=in_area_nlcd[key]["41"]
                        in42=in_area_nlcd[key]["42"]
                        in43=in_area_nlcd[key]["43"]
                        in52=in_area_nlcd[key]["52"]
                        in71=in_area_nlcd[key]["71"]
                        in81=in_area_nlcd[key]["81"]
                        in82=in_area_nlcd[key]["82"]
                        in90=in_area_nlcd[key]["90"]
                        in95=in_area_nlcd[key]["95"]
                        inDV=sum([in21,in22,in23,in24])
                        inUD=sum([in11,in31,in41,in42,
                                in43,in52,in71,in81,
                                in82,in90,in95])
                        inSum=sum([in21,in22,in23,in24,
                                in11,in31,in41,in42,
                                in43,in52,in71,in81,
                                in82,in90,in95])
                    else:
                        in11=0
                        in21=0
                        in22=0
                        in23=0
                        in24=0
                        in31=0
                        in41=0
                        in42=0
                        in43=0
                        in52=0
                        in71=0
                        in81=0
                        in82=0
                        in90=0
                        in95=0
                        inDV=0
                        inUD=0
                        inSum=0
                    # grab the out
                    if key in out_area_nlcd.keys():
                        out11=out_area_nlcd[key]["11"]
                        out21=out_area_nlcd[key]["21"]
                        out22=out_area_nlcd[key]["22"]
                        out23=out_area_nlcd[key]["23"]
                        out24=out_area_nlcd[key]["24"]
                        out31=out_area_nlcd[key]["31"]
                        out41=out_area_nlcd[key]["41"]
                        out42=out_area_nlcd[key]["42"]
                        out43=out_area_nlcd[key]["43"]
                        out52=out_area_nlcd[key]["52"]
                        out71=out_area_nlcd[key]["71"]
                        out81=out_area_nlcd[key]["81"]
                        out82=out_area_nlcd[key]["82"]
                        out90=out_area_nlcd[key]["90"]
                        out95=out_area_nlcd[key]["95"]
                        outDV=sum([out21,out22,out23,out24])
                        outUD=sum([out11,out31,out41,out42,
                                out43,out52,out71,out81,
                                out82,out90,out95])
                        outSum=sum([out21,out22,out23,out24,
                                    out11,out31,out41,out42,
                                    out43,out52,out71,out81,
                                    out82,out90,out95])
                    else:
                        out11=0
                        out21=0
                        out22=0
                        out23=0
                        out24=0
                        out31=0
                        out41=0
                        out42=0
                        out43=0
                        out52=0
                        out71=0
                        out81=0
                        out82=0
                        out90=0
                        out95=0
                        outDV=0
                        outUD=0
                        outSum=0
                    
                    data = {
                        "11": {"in": in11, "out": out11, "tot": tot11},
                        "21": {"in": in21, "out": out21, "tot": tot21},
                        "22": {"in": in22, "out": out22, "tot": tot22},
                        "23": {"in": in23, "out": out23, "tot": tot23},
                        "24": {"in": in24, "out": out24, "tot": tot24},
                        "31": {"in": in31, "out": out31, "tot": tot31},
                        "41": {"in": in41, "out": out41, "tot": tot41},
                        "42": {"in": in42, "out": out42, "tot": tot42},
                        "43": {"in": in43, "out": out43, "tot": tot43},
                        "52": {"in": in52, "out": out52, "tot": tot52},
                        "71": {"in": in71, "out": out71, "tot": tot71},
                        "81": {"in": in81, "out": out81, "tot": tot81},
                        "82": {"in": in82, "out": out82, "tot": tot82},
                        "90": {"in": in90, "out": out90, "tot": tot90},
                        "95": {"in": in95, "out": out95, "tot": tot95},
                        "DV": {"in": inDV, "out": outDV, "tot": totDV},
                        "UD": {"in": inUD, "out": outUD, "tot": totUD},
                    }
                    results={}
                    for cls, values in data.items():
                        in_var = values["in"]
                        out_var = values["out"]
                        tot_var = values["tot"]
                        # Check and correct if `in + out != tot`
                        if in_var + out_var != tot_var:
                            halfdiff = (tot_var - (in_var + out_var)) / 2
                            in_var += halfdiff
                            out_var += halfdiff
                        try:
                            # Proportion calculations
                            prop_tot = float(tot_var) / float(totSum) if totSum else 0
                            prop_in = float(in_var) / float(tot_var) if tot_var else 0
                            prop_out = float(out_var) / float(tot_var) if tot_var else 0
                        except (ValueError, TypeError):
                            prop_tot = 0
                            prop_in = 0
                            prop_out = 0
                        results[cls] = {
                            "propTot": prop_tot,
                            "propIn": prop_in,
                            "propOut": prop_out
                        }
                    
                    # Start index for row numbers
                    row_index = 1

                    # Populate the row dynamically
                    for cls in nlcd_categories:
                        row[row_index] = data[cls]["tot"]
                        row[row_index + 1] = data[cls]["in"]
                        row[row_index + 2] = data[cls]["out"]
                        row[row_index + 3] = results[cls]["propTot"]
                        row[row_index + 4] = results[cls]["propIn"]
                        row[row_index + 5] = results[cls]["propOut"]

                        # Increment the row index by 6 for the next class
                        row_index += 6
                    # finally, update fc
                    cursor.updateRow(row)        
        def process_hisdac_fields(fc,hisdac_fields,tot_area_hisdac,in_area_hisdac,out_area_hisdac):
            with arcpy.da.UpdateCursor(fc,hisdac_fields) as cursor:
                for row in cursor:
                    key=row[0]
                    # grab the totals
                    if key in tot_area_hisdac.keys():
                        totDV=tot_area_hisdac[key]["1"]
                        totUD=tot_area_hisdac[key]["0"]            
                        totSum=sum([totDV,totUD])
                    else:            
                        totDV=0
                        totUD=0
                        totSum=0
                    
                    # grab the in
                    if key in in_area_hisdac.keys():
                        inDV=in_area_hisdac[key]["1"]
                        inUD=in_area_hisdac[key]["0"]            
                        inSum=sum([inDV,inUD])
                    else:            
                        inDV=0
                        inUD=0
                        inSum=0
                    # grab the out
                    if key in out_area_hisdac.keys():
                        outDV=out_area_hisdac[key]["1"]
                        outUD=out_area_hisdac[key]["0"]            
                        outSum=sum([outDV,outUD])
                    else:            
                        outDV=0
                        outUD=0
                        outSum=0
                    
                    data = {
                        "DV": {"in": inDV, "out": outDV, "tot": totDV},
                        "UD": {"in": inUD, "out": outUD, "tot": totUD}            
                    }
                    results={}
                    for cls, values in data.items():
                        in_var = values["in"]
                        out_var = values["out"]
                        tot_var = values["tot"]
                        # Check and correct if `in + out != tot`
                        if in_var + out_var != tot_var:
                            halfdiff = (tot_var - (in_var + out_var)) / 2
                            in_var += halfdiff
                            out_var += halfdiff
                        try:
                            # Proportion calculations
                            prop_tot = float(tot_var) / float(totSum) if totSum else 0
                            prop_in = float(in_var) / float(tot_var) if tot_var else 0
                            prop_out = float(out_var) / float(tot_var) if tot_var else 0
                        except (ValueError, TypeError):
                            prop_tot = 0
                            prop_in = 0
                            prop_out = 0
                        results[cls] = {
                            "propTot": prop_tot,
                            "propIn": prop_in,
                            "propOut": prop_out
                        }
                    
                    # Start index for row numbers
                    row_index = 1

                    # Populate the row dynamically
                    for cls in ["DV","UD"]:
                        row[row_index] = data[cls]["tot"]
                        row[row_index + 1] = data[cls]["in"]
                        row[row_index + 2] = data[cls]["out"]
                        row[row_index + 3] = results[cls]["propTot"]
                        row[row_index + 4] = results[cls]["propIn"]
                        row[row_index + 5] = results[cls]["propOut"]

                        # Increment the row index by 6 for the next class
                        row_index += 6
                    # finally, update fc
                    cursor.updateRow(row)
        def allocatePopulation(fc,pop_fields):
            with arcpy.da.UpdateCursor(fc,pop_fields+["TOTPOP","PROP_IN","PROP_OUT","BUAPIN_DV","BUAPOUT_DV","NPIN_DV","NPOUT_DV"]) as cursor:
                for row in cursor:
                    key=row[0]
                    # grab proportions
                    tot_pop=row[10]
                    prop_in=row[11]
                    prop_out=row[12]
                    bua_prop_in=row[13]
                    bua_prop_out=row[14]
                    nlcd_prop_in=row[15]
                    nlcd_prop_out=row[16]
                    # calculate allocations
                    uniform_in=max(0, float(tot_pop) * float(prop_in))
                    uniform_out=max(0, float(tot_pop) * float(prop_out))
                    bua_in=max(0, float(tot_pop) * float(bua_prop_in))
                    bua_out=max(0, float(tot_pop) * float(bua_prop_out))
                    nlcd_in=max(0, float(tot_pop) * float(nlcd_prop_in))
                    nlcd_out=max(0, float(tot_pop) * float(nlcd_prop_out))        
                    # add to FC
                    row[1] = tot_pop
                    row[2] = tot_pop
                    row[3] = tot_pop
                    row[4] = uniform_in        
                    row[5] = bua_in        
                    row[6] = nlcd_in
                    row[7] = uniform_out
                    row[8] = bua_out
                    row[9] = nlcd_out
                    # finally, update fc
                    cursor.updateRow(row)
        
        # Define categories
        hisdac_numeric_categories = {"0", "1"}
        nlcd_numeric_categories = {"11", "21", "22", "23", "24", "31", "41", "42", "43", "52", "71", "81", "82", "90", "95"}

        # Define special categories
        nlcd_special_categories = {
            "DV": ["21", "22", "23", "24"],  # Developed categories
            "UD": ["11", "31", "41", "42", "43", "52", "71", "81", "82", "90", "95"]  # Undeveloped categories
        }
        # HISDAC Field Definitions
        hisdac_field_types = ["BUATOT_", "BUAIN_", "BUAOUT_", "BUAPTOT_", "BUAPIN_", "BUAPOUT_"]
        hisdac_categories = ["DV","UD"]

        # NLCD Field Definitions
        nlcd_field_types = ["NTOT_", "NIN_", "NOUT_", "NPTOT_", "NPIN_", "NPOUT_"]
        nlcd_categories = ["11", "21", "22", "23", "24", "31", "41", "42", "43", "52", "71", "81", "82", "90", "95", "DV", "UD"]

        # POP Field Definitions
        pop_field_types = ["CPOP_","HPOP_","NPOP_"]
        pop_categories= ["TOT","IN","OUT"]

        # File paths for HISDAC
        dissolveFC_hisdac = os.path.join(output_dirs["dissolve"], "hisdac_"+os.path.basename(fc))
        inHisdac = os.path.join(output_dirs["clip_in"], f"hisdac_{os.path.basename(fc)}")
        outHisdac = os.path.join(output_dirs["clip_out"], f"hisdac_{os.path.basename(fc)}")

        # File paths for NLCD
        dissolveFC_nlcd = os.path.join(output_dirs["dissolve"], "nlcd_"+os.path.basename(fc))
        inNLCD = os.path.join(output_dirs["clip_in"], f"nlcd_{os.path.basename(fc)}")
        outNLCD = os.path.join(output_dirs["clip_out"], f"nlcd_{os.path.basename(fc)}")

        # Populate dictionaries for HISDAC
        tot_area_hisdac = populate_area_dict(dissolveFC_hisdac, ["GISJOIN", "gridcode", "SUM_BUA_TO"], hisdac_numeric_categories)
        in_area_hisdac = populate_area_dict(inHisdac, ["GISJOIN", "gridcode", "BUA_IN"], hisdac_numeric_categories)
        out_area_hisdac = populate_area_dict(outHisdac, ["GISJOIN", "gridcode", "BUA_OUT"], hisdac_numeric_categories)    

        # Populate dictionaries for NLCD
        tot_area_nlcd = populate_area_dict(dissolveFC_nlcd, ["GISJOIN", "gridcode", "SUM_NLCD_T"], nlcd_numeric_categories, nlcd_special_categories)
        in_area_nlcd = populate_area_dict(inNLCD, ["GISJOIN", "gridcode", "NLCD_IN"], nlcd_numeric_categories, nlcd_special_categories)
        out_area_nlcd = populate_area_dict(outNLCD, ["GISJOIN", "gridcode", "NLCD_OUT"], nlcd_numeric_categories, nlcd_special_categories)    

        # Add Fields
        hisdac_fields = add_fields_to_feature_class(fc, hisdac_field_types, hisdac_categories)
        nlcd_fields = add_fields_to_feature_class(fc, nlcd_field_types, nlcd_categories)
        pop_fields = add_fields_to_feature_class(fc, pop_field_types, pop_categories)

        # process the data
        process_hisdac_fields(fc,hisdac_fields,tot_area_hisdac,in_area_hisdac,out_area_hisdac)
        process_nlcd_fields(fc,nlcd_fields,tot_area_nlcd,in_area_nlcd,out_area_nlcd,nlcd_categories)
        allocatePopulation(fc,pop_fields)
        print("Allocated population for " + fc)
        return(1,"Allocated population for  " + fc)
    except:
        print(str(traceback.format_exc()))
        return(0,str(traceback.format_exc()))
def geoprocess_county(fc):  
    try:      
        dissolve_county =os.path.join(output_dirs["county"], os.path.basename(fc).replace("block","county"))
        arcpy.PairwiseDissolve_analysis(fc, dissolve_county, "FIPSSTCO", [["TOTPOP", "SUM"],["ALAND", "SUM"],
                                                                        ["AREA_TOT", "SUM"],["AREA_IN", "SUM"],["AREA_OUT", "SUM"],
                                                                        ["CPOP_TOT", "SUM"],["CPOP_IN", "SUM"],["CPOP_OUT", "SUM"],
                                                                        ["BUATOT_DV", "SUM"],["BUAIN_DV", "SUM"],["BUAOUT_DV", "SUM"],
                                                                        ["HPOP_TOT", "SUM"],["HPOP_IN", "SUM"],["HPOP_OUT", "SUM"],
                                                                        ["NTOT_DV", "SUM"],["NIN_DV", "SUM"],["NOUT_DV", "SUM"],
                                                                        ["NPOP_TOT", "SUM"],["NPOP_IN", "SUM"],["NPOP_OUT", "SUM"],], "MULTI_PART")

        summaryFields=["TOTPOP","ALAND",
                    "AREA_TOT","AREA_IN","AREA_OUT",
                    "CPOP_TOT","CPOP_IN","CPOP_OUT",
                    "BUATOT_DV","BUAIN_DV","BUAOUT_DV",
                    "HPOP_TOT","HPOP_IN","HPOP_OUT",
                    "NTOT_DV","NIN_DV","NOUT_DV",
                    "NPOP_TOT","NPOP_IN","NPOP_OUT"]

        for summaryField in summaryFields:
            oldField = "SUM_"+summaryField[:6]
            newField = summaryField
            arcpy.AddField_management(dissolve_county,newField,"DOUBLE")
            arcpy.CalculateField_management(dissolve_county,newField,"!"+oldField+"!","PYTHON")
            arcpy.DeleteField_management(dissolve_county,oldField)
        print("Geoprocessed County for " + fc)
        return(1,"Geoprocessed County for  " + fc)
    except:
        print(str(traceback.format_exc()))
        return(0,str(traceback.format_exc()))        
def clear_directory(directory_path, fc): 
    try:   
        if not os.path.exists(directory_path):
            return(0,f"Directory does not exist: {directory_path}")      
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.basename(fc)[:-4] in file_path:
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)  # Remove the file or symbolic link
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # Remove the directory and its contents
                except Exception as e:
                    return(0,f"Failed to delete {file_path}: {e}")
        print("Cleaned directory for " + directory_path)
        return(1,"Cleaned directory for  " + directory_path)
    except:
        print(str(traceback.format_exc()))
        return(0,str(traceback.format_exc()))

def process(fc):    
    # Create a unique scratch directory for this process
    scratch_workspace = os.path.join(output_dirs["scratch"], os.path.basename(fc)[:-4])
    if not arcpy.Exists(scratch_workspace):
        os.mkdir(scratch_workspace)
    arcpy.env.scratchWorkspace = scratch_workspace
    arcpy.env.workspace = scratch_workspace
    results=[]
    # uniform_proportions = calculate_uniform_proportions(fc)
    # if not uniform_proportions:
    #     return uniform_proportions
    # results.append(uniform_proportions)
    # geoprocess the data
    nlcdGP=geoprocess(fc, "nlcd",  "NLCD_TOT", "NLCD_IN", "NLCD_OUT")
    if not nlcdGP:
        return nlcdGP
    results.append(nlcdGP)
    hisdacGP=geoprocess(fc, "hisdac", "BUA_TOT", "BUA_IN", "BUA_OUT")
    if not hisdacGP:
        return hisdacGP
    results.append(hisdacGP)
    # allocate the population
    popAllocation=calculate_and_apply_allocations(fc)
    if not popAllocation:
        return popAllocation
    results.append(popAllocation)
    # finally lets aggregate to the county level
    countyGP=geoprocess_county(fc)
    if not countyGP:
        return countyGP
    results.append(countyGP)
    # # clean the directories
    # for key, directory_path in output_dirs.items():
    #     if key == "county":
    #         continue
    #     clear=clear_directory(directory_path,fc)
    #     if not clear:
    #         return clear
    #     results.append(clear)

    return(results)

def main():
    procList=[]
    # define input workspace containing merit files
    arcpy.env.workspace=base_path + os.sep +"blocks"
    fcs=arcpy.ListFeatureClasses("*")
    for fc in fcs:
        countyFile=os.path.join(output_dirs["county"], os.path.basename(fc).replace("block","county"))
        if not arcpy.Exists(countyFile):
            procList.append(os.path.join(base_path+ os.sep +"blocks",fc))
    print("processing using this number of files: " + str(len(procList)))   
    for p in procList:        
        print(p)
        print(process(p))
    #     print("Script Complete in " + str(datetime.datetime.now()-scriptTime))
    #     sys.exit()
        
    # this is for multicore processing        
    # pool = multiprocessing.Pool(processes=8,maxtasksperchild=1)# processes should = number of cores
    # results = pool.map(process, procList)
    # for result in results:
    #     print(result)
    # Synchronize the main process with the job processes to
    # ensure proper cleanup.
    # pool.close()
    # pool.join()
    print("Script Complete in " + str(datetime.datetime.now()-scriptTime))

if __name__ == '__main__':
    main()