# multiprocess template
import os, datetime
import multiprocessing
import arcpy, sys
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput=True
scriptTime = datetime.datetime.now()
# create scratch folder
def createScratch(iso):
    # create scratch directory
    scratchDir=r'F:\lecz\sample_processing\scratch'+os.sep+iso
    if not arcpy.Exists(scratchDir):
        os.mkdir(scratchDir)
    return scratchDir

## calculate the zonal statistics
def calcZstats(z):
    resultsList=[]
    outFolder=r'F:\lecz\zonal_stats_global_data_v3'
    year=os.path.basename(z)[7:11]
    #return((0,os.path.basename(z)[7:11]))
    #values
    if "mollweide" in z:
        valueWS=r'F:\lecz\values_global_data\mollweide'
    else:
        valueWS=r'F:\lecz\values_global_data\wgs84'
    arcpy.env.workspace=valueWS
    values=arcpy.ListRasters("*"+year+"*")    
    for v in values:  
        if "1km" in v:
            continue      
        outStats = outFolder+os.sep+os.path.basename(z)[:-4]+"_"+os.path.basename(v)[:-4]+".dbf"
        if arcpy.Exists(outStats):
             resultsList.append(outStats+ " already exists")
        # outStats=r'I:\leczv3\usa\zonal_stats_global_data\zonal.gdb'+os.sep+os.path.basename(z)+"_"+os.path.basename(v)[:-4]
        try:
            # template=r'I:\leczv3\usa\lecz_us_county_data.gdb\us_county_2010_with_lecz_census_attributes'
            # execute zonal statistics
            arcpy.sa.ZonalStatisticsAsTable(z,"FIPSSTCO",v,outStats,"DATA")
            # fieldName=os.path.basename(v)[:-4].replace("usa1_","")
            # resultsList.append(fieldName)
            # arcpy.AddField_management(outStats,fieldName,"DOUBLE")
            # arcpy.CalculateField_management(outStats,fieldName,"!SUM!","PYTHON")
            # arcpy.JoinField_management(template,"JOINCODE",outStats,"Value",[fieldName])
            resultsList.append("Created "+outStats)
##            break
        except:
##                if arcpy.Exists(outStats):
##                    arcpy.Delete_management(outStats)
            resultsList.append("Failed to create "+outStats+ " Error: " + arcpy.GetMessages())
##            break
    return(1,resultsList)


def process(rasterPath):
    # I have generally commented and run through 1 function at a time, checking the results
    # at each step in the process. There has been some apparent instabiity when I try to run
    # multiple countries in a batch across multiple functions.  Maybe a file lock issue somewhere, but I haven't been able to identify the source?
    # it works fine for 1 country and all functions, or many countries 1 function at a time. Why?
    resultsList=[]

    ## Calculate Zonal Statistics
    zstatResult=calcZstats(rasterPath)
    if zstatResult[0]==0:
        return (0,"ZStats",zstatResult)
    else:
        resultsList.append(zstatResult[1])

    return resultsList

def main():
     # define input workspace containing merit files
    workspace = r'F:\lecz\sample_processing\merge_raster'
    arcpy.env.workspace = workspace
    procList = [os.path.join(workspace,r)for r in arcpy.ListRasters("*mollweide*")]
##    ##TEMP
##    procList1 = [os.path.join(workspace,r)for r in arcpy.ListRasters("*")]
##    procList=[]
##    for rasterPath in procList1:
##        if os.path.basename(rasterPath).split("_")[0]=="can":
##            continue
##        elif os.path.basename(rasterPath).split("_")[0]=="ruse":
##            continue
##        else:
##            procList.append(rasterPath)
##    print len(procList)
##    procList=procList[0:40]
    
    print("processing using this number of processes: " + str(len(procList)))
    
    for p in procList:
        print(p)
        print(process(p))
    print("Script Complete in " + str(datetime.datetime.now()-scriptTime))
    sys.exit()
        
    ## this is for multicore processing        
##    pool = multiprocessing.Pool(processes=10,maxtasksperchild=1)# processes should = number of cores
##    results = pool.map(process, procList)
##    for result in results:
##        print result
##    # Synchronize the main process with the job processes to
##    # ensure proper cleanup.
##    pool.close()
##    pool.join()
    print("Script Complete in " + str(datetime.datetime.now()-scriptTime))
 
if __name__ == '__main__':
    main()
