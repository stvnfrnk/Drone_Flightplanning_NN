#!/usr/bin/env python

from osgeo import ogr,osr
from shapely import affinity, LineString, Polygon, Point, linearrings
import sys
import os
import zipfile
import shutil
import numpy as np
from bs4 import BeautifulSoup
import pylab as plt
from lxml import etree
import io

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


#N. Neckel 2024, script to constantly move DJI KMZ file to another location

#newlon, newlat = 8.7312689,53.5031708

if (len(sys.argv) > 1):
	infile = sys.argv[1]
	newlon = float(sys.argv[2])
	newlat = float(sys.argv[3])
	rotation = float(sys.argv[3])
	if newlat > 60:
		EPSG = 3413
	else:
		EPSG = 32632
		
	newpsx,newpsy,newpsz = TransCoordsLatLonToPS(EPSG).TransformPoint(float(newlon),float(newlat))

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

	#open waylines.wpml and translate coordinates to new position
	wpmzfile = open('wpmz/waylines.wpml', "r")
	contents = wpmzfile.read()
	soup = BeautifulSoup(contents, 'xml')
	speeds = soup.find_all('wpml:waypointSpeed')
	coordinates = soup.find_all('coordinates')
	duration = soup.find_all('wpml:duration')
	height = soup.find_all('wpml:executeHeight')
	coordlist = []
	for l in np.arange(len(coordinates)):
		lon = coordinates[l].text.split(',')[0]
		lat = coordinates[l].text.split(',')[1]
		alt = height[l].text
		psx,psy,psz = TransCoordsLatLonToPS(EPSG).TransformPoint(float(lon),float(lat),float(alt))
		coordlist.append([psx,psy,psz])
	LINE = linearrings(coordlist)
	xoff = LINE.centroid.x-newpsx
	yoff = LINE.centroid.y-newpsy
	translated_a = affinity.translate(LINE, xoff=-xoff, yoff=-yoff, zoff=0.0)
	coordlist = list(translated_a.coords)
	if rotation != 0:
		rotated_a = affinity.rotate(translated_a, rotation)
		coordlist = list(rotated_a.coords)

	#exchange coordinates in original waylines.wpml file
	ns = {"kml": "http://www.opengis.net/kml/2.2"}
	tree  = etree.parse('wpmz/waylines.wpml')
	i=0
	for coords in tree.xpath("/kml:kml/kml:Document/kml:Folder/kml:Placemark/kml:Point/kml:coordinates", namespaces=ns):
		lon,lat,alt = TransCoordsPSToLatLon(EPSG).TransformPoint(coordlist[i][0],coordlist[i][1],0)
		coords.text="{},{}".format(lon,lat)
		i=i+1
	for name in tree.xpath("/kml:kml/kml:Document/kml:name", namespaces=ns):
		name.text='tmp'
	with open('tmp.kml', 'wb') as f:
		f.write(etree.tostring(tree,encoding='utf-8', xml_declaration=True))
	f.close()
	os.system('mv tmp.kml wpmz/waylines.wpml')

	#open template.kml and translate polygon to new position
	wpmzfile = open('wpmz/template.kml', "r")
	contents = wpmzfile.read()
	soup = BeautifulSoup(contents, 'xml')
	poly = soup.find_all('Polygon')
	LinearRingList = []
	if len(poly) > 0:
		tag = poly[0].select('coordinates')[0]
		coordinates = tag.get_text().split()
		coordlist = []
		for l in np.arange(len(coordinates)):
			psx,psy,psz = TransCoordsLatLonToPS(EPSG).TransformPoint(float(coordinates[l].split(',')[0]),float(coordinates[l].split(',')[1]),float(coordinates[l].split(',')[2]))
			print(psx,psy,psz)
			coordlist.append((psx,psy,psz))
		POLYGON = linearrings(coordlist)
		xoff = POLYGON.centroid.x-newpsx
		yoff = POLYGON.centroid.y-newpsy
		translated_a = affinity.translate(POLYGON, xoff=-xoff, yoff=-yoff, zoff=0.0)
		coordlist = list(translated_a.coords)
		if rotation != 0:
			rotated_a = affinity.rotate(translated_a, rotation)
			coordlist = list(rotated_a.coords)
		LinearRingList.append(coordlist)

		ns = {"kml": "http://www.opengis.net/kml/2.2"}
		tree  = etree.parse('wpmz/template.kml')
		i=0
		for coords in tree.xpath("/kml:kml/kml:Document/kml:Folder/kml:Placemark/kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates", namespaces=ns):
			for u in LinearRingList:
				strlist = []
				for m in u:
					lon,lat,alt = TransCoordsPSToLatLon(EPSG).TransformPoint(m[0],m[1],m[2])
					strlist = np.append(strlist,(lon,lat,alt))
				strlist = strlist.reshape(int(len(strlist)/3),3)
				bio = io.BytesIO()
				np.savetxt(bio, strlist[:-1],fmt='%s',delimiter=',') #Only 4 coordinate pairs are needed for template.kml
				mystr = bio.getvalue().decode('latin1')
				coords.text="\n{}              ".format(mystr)
			for name in tree.xpath("/kml:kml/kml:Document/kml:name", namespaces=ns):
				name.text='tmp'
			with open('tmp.kml', 'wb') as f:
				f.write(etree.tostring(tree))
			f.close()
		os.system('mv tmp.kml wpmz/template.kml')
	if os.path.exists(infile[:-4]+'_shifted.kmz'):
		os.system('rm '+infile[:-4]+'_shifted.kmz')
	shutil.make_archive(infile[:-4]+'_shifted', 'zip', 'wpmz')
	if not os.path.exists('SHIFT'):
		os.mkdir('SHIFT')
	os.system('mv '+infile[:-4]+'_shifted.zip SHIFT/'+infile[:-4]+'.kmz')
	print('File {} succesfully shifted to {} {} and copied to SHIFT folder.'.format(infile,newlon,newlat))
else:
	print('###############################N.Neckel, 2024#############################################')
	print('#      Script to constantly move and/or rotate DJI KMZ file to another location          #')
	print('#      Usage:                                                                            #')
	print('#      01_constantly_move_grid.py DJI.kmz new_long new_lat rotation                      #')
	print('##########################################################################################')
