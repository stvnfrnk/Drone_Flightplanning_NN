from osgeo import ogr,osr
import numpy as np


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

def write_header(speed,outfile,altref):
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