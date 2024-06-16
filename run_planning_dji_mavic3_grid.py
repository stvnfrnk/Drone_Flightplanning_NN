
import numpy as np
import os, shutil
from drone_planning_functions import TransCoordsLatLonToPS, TransCoordsPSToLatLon
from drone_planning_functions import read_attribute, NewWaypoint, write_header

speed  = 5          # meters per second
pitch  = -90        # -90 is nadir
EPSG   = 32632      # EPSG
altref = 'WGS84'    # can be an integer "relativeToStartPoint" or "WGS84" 

# Path where shapefile with points are stored
top_path = "C:\\Users\\sfranke\\Seafile\\Orca\\Projects\\Vernagtferner\\2024\\flightplanner\\testcase_blockland\\"

# Input poits where to take pictures
inshape = top_path + "SCHW_2_projection_centres.shp"

# Filename for the final output file and folder on the controller
filename = top_path + '59CB6FB3-005E-433D-B8F8-2BA8C39A4C35____TEST'

# define wpmz directory and waylines.wpml file
wpmz_dir = top_path + "wpmz"
outfile  = top_path + "wpmz\\waylines.wpml"

# Open output file in "write" mode
outfile = open(outfile ,'w')

# Write KML file header
write_header(speed,outfile,altref)

# Read fotonumbers, coords and absolute altitude above ground from shapefile
fotonums = np.array(read_attribute(inshape,1)).astype(int)
xcoords  = np.array(read_attribute(inshape,2)).astype(float)
ycoords  = np.array(read_attribute(inshape,3)).astype(float)
altasl   = np.array(read_attribute(inshape,4)).astype(float)

# Rearrange order to follow the fotonumber increment
grid = np.stack((fotonums,xcoords,ycoords,altasl),axis=1)
grid = grid[np.argsort(grid[:,0])]

# Convert coordinates to Lon, Lat
# Create KML block for a new waypoint
for i in np.arange(len(fotonums)):
	lon,lat,alt = TransCoordsPSToLatLon(EPSG).TransformPoint(grid[i,1],grid[i,2],grid[i,3])
	NewWaypoint(lon,lat,int(grid[i,0]-1),alt,speed,outfile,pitch)

# Write KML file footer & close
outfile.write('    </Folder>\n')
outfile.write('  </Document>\n')
outfile.write('</kml>\n')
outfile.close()

# Remove file if exists
if os.path.exists(filename + '.kmz'):
	os.remove(filename + '.kmz')

# Compress (zip) the "wpmz" directory, where the waylines KML file is stored
shutil.make_archive(filename, 'zip', wpmz_dir)

# Rename ".zip" to ".kmz"
os.replace(filename + '.zip', filename + '.kmz')
