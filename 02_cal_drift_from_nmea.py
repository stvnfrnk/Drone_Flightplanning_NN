import numpy as np
import datetime as dt
import pylab as plt
from osgeo import ogr,osr
import os
import matplotlib.dates as mdates
from scipy import stats
import pandas as pd
from subprocess import Popen, PIPE

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

#N. Neckel 2024, script to calculate drift vector from handheld GPS connected to the Computer
#requires gpspipe so far only available under Linux

#print('Logging GPS for 10 Minutes...')
#cmd = 'gpspipe -r -x 600 > tmp'
#p = Popen(cmd, shell=True)
#p.wait()

inmea = open('tmp3.txt','r') #this is a dummy nmea string from a simulated drift
GPRMC = []
GPGGA = []
for line in inmea:
	if line.rstrip().startswith('$GPRMC'):
		tags = line.rstrip().split(',')
		time = tags[1]
		##convert latitude to decimal degrees
		lat = tags[3]
		Y = tags[4]
		DEG = lat[:2]
		MIN = lat[2:4]
		SEC = float('0.'+lat.split('.')[1])*60
		DD = float(DEG)+float(MIN)/60+SEC/3600
		if Y == 'S':
			DD = DD*-1
		lat = DD
		if lat < 60:
			EPSG = 32632
		else:			
			EPSG = 3413
		##convert longitude to decimal degrees
		lon = tags[5]
		X = tags[6]
		DEG = lon[:3]
		MIN = lon[3:5]
		SEC = float('0.'+lon.split('.')[1])*60
		DD = float(DEG)+float(MIN)/60+SEC/3600
		if X == 'W':
			DD = DD*-1
		lon = DD
		date = tags[9]
		date = date[:2]+date[2:4]+'20'+date[4:]
		GPSdatetime = dt.datetime.strptime(date+time, '%d%m%Y%H%M%S.%f')
		psx,psy,psz = TransCoordsLatLonToPS(EPSG).TransformPoint(lon,lat)
		GPRMC = np.append(GPRMC,lat)
		GPRMC = np.append(GPRMC,lon)
		GPRMC = np.append(GPRMC,GPSdatetime)
		GPRMC = np.append(GPRMC,psx)
		GPRMC = np.append(GPRMC,psy)
	if line.rstrip().startswith('$GPGGA'):
		tags = line.rstrip().split(',')
		time = tags[1]
		GPStime = dt.datetime.strptime(time, '%H%M%S.%f')
		sat = int(tags[7])
		prec = float(tags[8])
		alt = float(tags[11])
		GPGGA = np.append(GPGGA,GPStime)
		GPGGA = np.append(GPGGA,sat)
		GPGGA = np.append(GPGGA,prec)
		GPGGA = np.append(GPGGA,alt)
GPRMC = GPRMC.reshape(int(len(GPRMC)/5),5)
GPGGA = GPGGA.reshape(int(len(GPGGA)/4),4)

GPSALL = []
for i in np.arange(len(GPRMC)):
	for j in np.arange(len(GPGGA)):
		if GPRMC[i,2].time() == GPGGA[j,0].time():
			GPSALL = np.append(GPSALL,GPRMC[i,2]) #date
			GPSALL = np.append(GPSALL,GPRMC[i,0]) #lat
			GPSALL = np.append(GPSALL,GPRMC[i,1]) #lon
			GPSALL = np.append(GPSALL,GPRMC[i,3]) #psx
			GPSALL = np.append(GPSALL,GPRMC[i,4]) #psy
			GPSALL = np.append(GPSALL,GPGGA[j,3]) #alt
			GPSALL = np.append(GPSALL,GPGGA[j,1]) #sat
			GPSALL = np.append(GPSALL,GPGGA[j,2]) #prec
GPSALL = GPSALL.reshape(int(len(GPSALL)/8),8)
np.savetxt(GPSALL[0,0].strftime('%Y%m%dT%H%M%S')+'_'+GPSALL[-1,0].strftime('%Y%m%dT%H%M%S')+'.txt',GPSALL, fmt='%s', delimiter=';', newline='\n', header='date time;lat;lon;x;y;alt;sats;prec', footer='', comments='', encoding=None)
os.system('mv tmp '+GPSALL[0,0].strftime('%Y%m%dT%H%M%S')+'_'+GPSALL[-1,0].strftime('%Y%m%dT%H%M%S')+'.NMEA')

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(10, 8))

#convert datetime to total seconds
X = pd.to_datetime(GPSALL[:,0])
X = (X - X[0]).total_seconds()

ax1.set_title('vx')
ax1.plot(X,GPSALL[:,3], color='r')
vx, intercept_x, _, _, _ = stats.linregress(X.astype(np.float32), GPSALL[:,3].astype(np.float32))
x_trend = vx * X + intercept_x
ax1.plot(X, x_trend,'k--')
ax1.set_ylabel('x-coord (m)')
ax1.grid('True')

ax2.set_title('vy')
ax2.plot(X,GPSALL[:,4], color='g')
vy, intercept_y, _, _, _ = stats.linregress(X.astype(np.float32), GPSALL[:,4].astype(np.float32))
y_trend = vy * X + intercept_y
ax2.plot(X, y_trend,'k--')
ax2.set_ylabel('y-coord (m)')
ax2.grid('True')
vel = np.sqrt(vx**2 + vy**2)

print('####Velocity from trendlines####')
print('vx: {} m/s'.format(round(vx,2)))
print('vy: {} m/s'.format(round(vy,2)))
print('vel: {} m/s'.format(round(vel,2)))

print('####Velocity from average dists#')
dx = np.diff(GPSALL[:,3].astype(np.float32))
dy = np.diff(GPSALL[:,4].astype(np.float32))
dt = np.diff(X)
vx = dx/dt
vy = dy/dt
vel = np.sqrt(np.mean(dx)**2 + np.mean(dy)**2) / np.mean(dt)
print('vx: {} m/s'.format(round(np.mean(vx),2)))
print('vy: {} m/s'.format(round(np.mean(vy),2)))
print('vel: {} m/s'.format(round(vel,2)))

ax3.set_title('vz')
ax3.plot(X,GPSALL[:,5], color='b')
ax3.set_ylabel('z-coord (m)')
ax3.set_xlabel('time (seconds)')
ax3.grid('True')
plt.tight_layout()
plt.savefig('drift_trend.png',dpi=300)
plt.show()
