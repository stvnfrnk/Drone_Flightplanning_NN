#!/usr/bin/env python

from osgeo import ogr,osr
from shapely.geometry import Point
import sys
import os
import zipfile
import shutil
import numpy as np
from bs4 import BeautifulSoup
import pylab as plt
from lxml import etree

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

#N. Neckel 2024, script to drift correct DJI KMZ file before uploading to drone
#dirft vector needs to be in m/s as calculated form 02_cal_dirft_from_nmea.py

if (len(sys.argv) > 1):
	infile = sys.argv[1]
	vx = float(sys.argv[2])
	vy = float(sys.argv[3])

	if os.path.exists('wpmz'):
		print('removing existing wpmz folder...')
		os.system('rm -r wpmz')

	with zipfile.ZipFile(infile, 'r') as zip_ref:
		print('extracting {}...'.format(infile))
		zip_ref.extractall()
		if not os.path.exists('wpmz'):
			os.mkdir('wpmz')
			os.system('mv template.kml wpmz/')
			os.system('mv waylines.wpml wpmz/')
	
	wpmzfile = open('wpmz/waylines.wpml', "r")
	contents = wpmzfile.read()
	soup = BeautifulSoup(contents, 'xml')
	speeds = soup.find_all('wpml:waypointSpeed')
	coordinates = soup.find_all('coordinates')
	duration = soup.find_all('wpml:duration')
	flightinfo = []
	for l in np.arange(len(coordinates)):
		lon = coordinates[l].text.split(',')[0]
		lat = coordinates[l].text.split(',')[1]
		if float(lat) > 60:
			EPSG = 3413
		else:
			EPSG = 32632
		psx,psy,psz = TransCoordsLatLonToPS(EPSG).TransformPoint(float(lon),float(lat),0)
		point1 = Point(psx,psy)
		flightinfo = np.append(flightinfo,psx)
		flightinfo = np.append(flightinfo,psy)
		flightinfo = np.append(flightinfo,speeds[l])
		if l == 0:
			flightinfo = np.append(flightinfo,0)
		else:
			lon_pre = coordinates[l-1].text.split(',')[0]
			lat_pre = coordinates[l-1].text.split(',')[1]
			psx_pre,psy_pre,psz_pre = TransCoordsLatLonToPS(EPSG).TransformPoint(float(lon_pre),float(lat_pre),0)
			point2 = Point(psx_pre,psy_pre)
			dist = point1.distance(point2)
			flightinfo = np.append(flightinfo,dist)
	flightinfo = (flightinfo.reshape(int(len(flightinfo)/4),4)).astype(float)
	totaldist = np.sum(flightinfo[:,3])
	meanspeed = np.mean(flightinfo[:,2])
	if len(duration) != 0:
		flighttime = float(duration[0].text)
	else:
		flighttime = totaldist/meanspeed
	cumdists = np.cumsum(flightinfo[:,3])
	flighttimes = np.linspace(0,flighttime,len(cumdists))
	
	vxlist = np.linspace(0,vx*len(cumdists),len(cumdists))
	vylist = np.linspace(0,vy*len(cumdists),len(cumdists))
	newx = flightinfo[:,0]+vxlist
	newy = flightinfo[:,1]+vylist
	newdist = []
	for l in np.arange(len(coordinates)):
		point1 = Point(newx[l],newy[l])
		if l == 0:
			newdist = np.append(newdist,0)
		else:
			point2 = Point(newx[l-1],newy[l-1])
			newdist = np.append(newdist,point1.distance(point2))
	plt.figure()
	plt.plot(flightinfo[:,0],flightinfo[:,1],label='original pattern')
	plt.plot(newx,newy,label='drift corrected pattern')
	plt.xlabel('x-coord (m)')
	plt.ylabel('y-coord (m)')
	plt.grid('True')
	plt.legend(loc='best')
	plt.tight_layout()
	plt.show()

	ns = {"kml": "http://www.opengis.net/kml/2.2"}
	tree  = etree.parse('wpmz/waylines.wpml')
	i=0
	for coords in tree.xpath("/kml:kml/kml:Document/kml:Folder/kml:Placemark/kml:Point/kml:coordinates", namespaces=ns):
		lon,lat,alt = TransCoordsPSToLatLon(EPSG).TransformPoint(newx[i],newy[i],0)
		coords.text="{},{}".format(lon,lat)
		i=i+1
	for name in tree.xpath("/kml:kml/kml:Document/kml:name", namespaces=ns):
		name.text='tmp'
	with open('tmp.kml', 'wb') as f:
		f.write(etree.tostring(tree))
	f.close()
	os.system('mv tmp.kml wpmz/waylines.wpml')
	if os.path.exists(infile[:-4]+'_drift.kmz'):
		os.system('rm '+infile[:-4]+'_drift.kmz')
	shutil.make_archive(infile[:-4]+'_drift', 'zip', 'wpmz')
	if not os.path.exists('DRIFT'):
		os.mkdir('DRIFT')
	os.system('mv '+infile[:-4]+'_drift.zip DRIFT/'+infile[:-4]+'.kmz')
	print('File {} succesfully corrected for drift and copied to DRIFT folder.'.format(infile))
else:
	print('###############################N.Neckel, 2024#############################################')
	print('#      Script to drift correct DJI KMZ file before uploading to drone                    #')
	print('#      Dirft vector needs to be in m/s as calculated form 02_cal_dirft_from_nmea.py      #')
	print('#      Usage:                                                                            #')
	print('#      03_drift_corr_grid.py vx vy                                                       #')
	print('##########################################################################################')
