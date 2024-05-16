#!/usr/bin/env python

from osgeo import ogr,osr
import datetime
import numpy as np
import shutil
import os

def TransCoordsLatLonToPS(EPSG):
	srs_in = osr.SpatialReference()
	srs_in.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
	srs_in.ImportFromEPSG(4326)
	srs_out = osr.SpatialReference()
	srs_out.ImportFromEPSG(EPSG)
	ct = osr.CoordinateTransformation(srs_in,srs_out)
	return ct

def TransCoordsPSToLatLon(EPSG):
	srs_in_back = osr.SpatialReference()
	srs_in_back.ImportFromEPSG(EPSG)
	srs_out_back = osr.SpatialReference()
	srs_out_back.ImportFromEPSG(4326)
	srs_out_back.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
	ct_back = osr.CoordinateTransformation(srs_in_back,srs_out_back)
	return ct_back
	
def read_attribute(shapefile,row):
	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(shapefile)
	layer = dataSource.GetLayer(0)
	attributelist = []
	for feature in layer:
		attribute = feature.GetField(row)
		attributelist.append(attribute)
	return attributelist
	
def NewWaypoint(lon,lat,no,alt,speed,outfile,pitch):
	outfile.write('      <Placemark>\n')
	outfile.write('        <Point>\n')
	outfile.write('          <coordinates>\n')
	outfile.write('            {},{}\n'.format(lon,lat))
	outfile.write('          </coordinates>\n')
	outfile.write('        </Point>\n')
	outfile.write('        <wpml:index>{}</wpml:index>\n'.format(no))
	outfile.write('        <wpml:executeHeight>{}</wpml:executeHeight>\n'.format(alt))
	outfile.write('        <wpml:waypointSpeed>{}</wpml:waypointSpeed>\n'.format(speed))
	outfile.write('        <wpml:waypointHeadingParam>\n')
	outfile.write('          <wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode>\n')
	outfile.write('        </wpml:waypointHeadingParam>\n')
	outfile.write('        <wpml:waypointTurnParam>\n')
	outfile.write('          <wpml:waypointTurnMode>toPointAndPassWithContinuityCurvature</wpml:waypointTurnMode>\n')
	outfile.write('          <wpml:waypointTurnDampingDist>0</wpml:waypointTurnDampingDist>\n')
	outfile.write('        </wpml:waypointTurnParam>\n')
	outfile.write('        <wpml:actionGroup>\n')
	outfile.write('          <wpml:actionGroupId>0</wpml:actionGroupId>\n')
	outfile.write('          <wpml:actionGroupStartIndex>{}</wpml:actionGroupStartIndex>\n'.format(no))
	outfile.write('          <wpml:actionGroupEndIndex>{}</wpml:actionGroupEndIndex>\n'.format(no))
	outfile.write('          <wpml:actionGroupMode>sequence</wpml:actionGroupMode>\n')#can be parallel or sequence
	outfile.write('          <wpml:actionTrigger>\n')
	outfile.write('            <wpml:actionTriggerType>reachPoint</wpml:actionTriggerType>\n')
	outfile.write('          </wpml:actionTrigger>\n')
	outfile.write('          <wpml:action>\n') ###1st action at waypoint pitch gimbal
	outfile.write('            <wpml:actionId>0</wpml:actionId>\n')
	outfile.write('            <wpml:actionActuatorFunc>gimbalEvenlyRotate</wpml:actionActuatorFunc>\n')#gimbalRotate?
	outfile.write('            <wpml:actionActuatorFuncParam>\n')
	outfile.write('              <wpml:gimbalPitchRotateAngle>{}</wpml:gimbalPitchRotateAngle>\n'.format(pitch))
	outfile.write('              <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>\n')
	outfile.write('            </wpml:actionActuatorFuncParam>\n')
	outfile.write('          </wpml:action>\n')
	outfile.write('          <wpml:action>\n') ###2nd action take photo
	outfile.write('            <wpml:actionId>1</wpml:actionId>\n')
	outfile.write('            <wpml:actionActuatorFunc>takePhoto</wpml:actionActuatorFunc>\n')
	outfile.write('            <wpml:actionActuatorFuncParam>\n')
	outfile.write('              <wpml:fileSuffix>IMAGE_{}</wpml:fileSuffix>\n'.format(no+1))
	outfile.write('              <wpml:payloadPositionIndex>0</wpml:payloadPositionIndex>\n')
	outfile.write('            </wpml:actionActuatorFuncParam>\n')
	outfile.write('          </wpml:action>\n')
	outfile.write('        </wpml:actionGroup>\n')
	outfile.write('      </Placemark>\n')

speed = 5
inshape = 'ROIUTM32_waypoints.shp'
EPSG = 32632
altref = 'WGS84' #relativeToStartPoint
pitch = -90
filename = '180D5472-7CD5-4DBE-96A8-F4B7B2336369'

outfile = open('wpmz/waylines.wpml','w')
outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
outfile.write('<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2">\n')
outfile.write('  <Document>\n')
outfile.write('    <wpml:missionConfig>\n')
outfile.write('      <wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode>\n')
outfile.write('      <wpml:finishAction>goHome</wpml:finishAction>\n')
outfile.write('      <wpml:exitOnRCLost>executeLostAction</wpml:exitOnRCLost>\n')
outfile.write('      <wpml:executeRCLostAction>goBack</wpml:executeRCLostAction>\n')
outfile.write('      <wpml:globalTransitionalSpeed>{}</wpml:globalTransitionalSpeed>\n'.format(speed))
outfile.write('      <wpml:droneInfo>\n')
outfile.write('        <wpml:droneEnumValue>68</wpml:droneEnumValue>\n')
outfile.write('        <wpml:droneSubEnumValue>0</wpml:droneSubEnumValue>\n')
outfile.write('      </wpml:droneInfo>\n')
outfile.write('    </wpml:missionConfig>\n')
outfile.write('    <Folder>\n')
outfile.write('      <wpml:templateId>0</wpml:templateId>\n')
outfile.write('      <wpml:executeHeightMode>{}</wpml:executeHeightMode>\n'.format(altref))
outfile.write('      <wpml:waylineId>0</wpml:waylineId>\n')
outfile.write('      <wpml:autoFlightSpeed>{}</wpml:autoFlightSpeed>\n'.format(speed))

fotonums = np.array(read_attribute(inshape,1)).astype(int)
xcoords = np.array(read_attribute(inshape,2)).astype(float)
ycoords = np.array(read_attribute(inshape,3)).astype(float)
altasl = np.array(read_attribute(inshape,4)).astype(float)
grid = np.stack((fotonums,xcoords,ycoords,altasl),axis=1)
grid = grid[np.argsort(grid[:,0])]
for i in np.arange(len(fotonums)):
	lon,lat,alt = TransCoordsPSToLatLon(EPSG).TransformPoint(grid[i,1],grid[i,2],grid[i,3])
	NewWaypoint(lon,lat,int(grid[i,0]-1),alt,speed,outfile,pitch)
outfile.write('    </Folder>\n')
outfile.write('  </Document>\n')
outfile.write('</kml>\n')
outfile.close()
if os.path.exists(filename+'.kmz'):
	os.system('rm '+filename+'.kmz')
shutil.make_archive(filename, 'zip', 'wpmz')
os.system('mv '+filename+'.zip '+filename+'.kmz')
