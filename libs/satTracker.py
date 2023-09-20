
from pyorbital.orbital import Orbital
from datetime import datetime, timedelta
from time import strftime, gmtime, localtime
import geopy.distance
from libs import Nexstar as ns
import time, os, socket, sys
class SatTracker():

    port=None
    socket=None

    # For satelite
    minElevation=0

    satName=None

    # Home position
    lat=0.0
    lon=0.0
    alt=0.0

    # I dont find it necessary
    # AOS sound
    sound=None

    # Prior to hardware movement of telescope
    minMountElevation=0

    # Custom TLE (Two Line Elements) file for offline use
    tle_file=None
    
    # UTC
    delta=datetime.now()- datetime.utcnow()
    delta=str(delta).strip(":")[0]
    offset=timedelta(hours=int(delta))  # timedelta is used for calculating diff betn two datees
    
    # Predicts pass time of satelite
    def passes(self, orb):
        dats=[]

        horizon=self.minElevation
        # Calculate passes for the next hours for a given start time and a given observer.
        NextPasses=orb.get_next_passes(datetime.utcnow(), 24, self.lon, self.lat, self.alt, horizon)

        for Pass in NextPasses:
            RiseTime, FallTime, MaxEle=Pass
            dats.append({
                "satName":self.satName,
                "startPass":str(RiseTime+self.offset),
                "endPass":str(FallTime+ self.offset),
                "maxEle":str(MaxEle +self.offset)
            })
        return dats
    
    # Pass time for each satelite
    def satPasses(self, satList):
        Pass=[]

        for satName in satList:
            self.satName=satName
            orb=self.checkTle()
            dats=self.passes(orb)

            for pAss in dats:
                Pass.append(pAss)
        return Pass
    # Use custom tle or use Internet
    def checkTle(self):
         if self.tle_file is not None:
            try:
                orb=Orbital(self.satName, tle_file=self.tle_file)
            except KeyError:
                print("Satelite Not Found Offline")
                sys.exit(0)
            
         else:
             try:
                orb = Orbital(self.satName)
             except KeyError:
                print("Satalite Not Found Online.")
                sys.exit(0)

         return orb
    # Azimuth is the angle betn celestial body (sun, moon) and the north, measured clockwise around the observer's horizon
    # Measure the position of satelite
    def satAzimuth(self, orb):
        now=datetime.utcnow()
        return orb.get_observer_look(now, self.lon, self.lat, self.alt)
    
    # Latitude and Longitude
    def satLatLon(self, orb):
        now=datetime.utcnow()
        return orb.get_lonlatalt(now)
    
    def currentTime(self):
        local=datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        return local
    
    # Distance of the sat from ground station
    def satDistance(self, lon,lat):
        Satelite=(lat, lon)
        Ground_Station=(self.lat, self.lon)
        DistanceInMiles=geopy.distance.distance(Satelite, Ground_Station).miles
        DistanceInKm=geopy.distance.distance(Satelite, Ground_Station).km
        return int(DistanceInMiles), int(DistanceInKm)
    
    # Calculate direction of sat
    def direction_lookup(self, degrees_temp):
        if degrees_temp < 0:
            final_degrees=degrees_temp + 360
        else:
            final_degrees=degrees_temp
        in_compass=["North", "North East", "East", "South East", "South", "South West", "West", "North West"]
        compass_lookup=round(final_degrees/ 45)
        return in_compass[int(compass_lookup)]
    
    # Determine direction of sat
    def satDirection(self, azimuth):
        return self.direction_lookup(azimuth)

    # Connect to TCP server
    def connectClient(self, address, port):
        try:
            client=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((address, int(port)))
            return client
        except:
            print("Cant connect to server")
            time.sleep(1)
            self.socket=False

    # Send data to TCP server
    def sendData(self, client, lon, lat, alt):
        try: 
            message="{},{: 2f},{: 2f},{: 2f}".format(self.satName, lon, lat,alt)
            client.send(message.encode())
        except:
            print("Failed to send")
            self.socket=False

    # Show result
    def showResult(self, orb, currLocal, startPass, endPass, maxEle):
        os.system("cls || clear")

        print("Tracking: {}". format(self.satName))
        print("Time: {} (UTC +{})".format(currLocal, self.offset))
        print("AOS: {}".format(startPass))
        print("MAX: {}".format(maxEle))
        print("LOS: {}".format(endPass))
        lat, lon, alt=self.satLatLon(orb)
        print("Latitude: {}\n Longitude: {}".format(lat, lon))
        print("Altitude: {:.2f}".format(alt))
        miles, km= self.satDistance(lat, lon)
        print("Distance in miles: {}".format(miles))
        print("Distance in Km: {}".format(km))

        
        azi, ele=self.satAzimuth(orb)
        heading=self.satDirection(azi)
        print("Approaching from: {}".format(heading))
        print("Azimuth: {:.2f}".format(azi))
        print("Elevation: {:.2f}".format(ele))
        return lat, lon,alt, ele,azi
    
    # Asemble
    def tracker(self, client, startPass, endPass, maxEle):
        orb=self.checkTle()
        while 1:
            currLocal=self.currentTime()
            startPass= startPass.split(".")[0]
            maxEle=maxEle.split(".")[0]
            endPass= endPass.split(".")[0]

            lat, lon,alt, ele,azi=self.showResult(orb, currLocal, startPass, endPass, maxEle)

            if self.socket:
                self.sendData(client, lon, lat, alt)
            
            if currLocal >= endPass:
                break

            time.sleep(5)

    
