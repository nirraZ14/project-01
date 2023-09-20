from libs import satTracker
import argparse, time


# Show Menu

parser = argparse.ArgumentParser(
   add_help=False,
   formatter_class=argparse.RawDescriptionHelpFormatter, # This will fix description and epilog format
   epilog="Examples: %(prog)s -weather")

# Groundstation Location Information
parser.add_argument("-lat", dest="latitude", default=51.4844, help="Ground Station Latitude.")
parser.add_argument("-lon", dest="longitude", default=0.1302, help="Ground Station Longitude.")
parser.add_argument("-alt", dest="altitude", help="Ground Station Altitude.")

# Sats To Track
parser.add_argument("-weather", action="store_true", help="Weather Satalites: METEOR-M 2, NOAA 19, NOAA 18, NOAA 15.")
parser.add_argument("-meteorm2", action="store_true", help="Weather Satalites: METEOR-M 2")
parser.add_argument("-afsk", action="store_true", help="AFSK Packet: PCSAT (NO-44), ISS (ZARYA).")
parser.add_argument("-isszarya", action="store_true", help="AFSK Packet:ISS (ZARYA).")
parser.add_argument("-elevation", dest="elevation", default=10, help="Minimum Satalite Elevation For Prediction.")
#
# Define The Parser
#
args = parser.parse_args()


#if args.check:

   #self.mountGoHome(controller)
if args.weather:

   satList = ["METEOR-M 2", "NOAA 19", "NOAA 18", "NOAA 15"]
elif args.meteorm2:
   satList=["METEOR-M 2"]
elif args.isszarya:
   satList=["ISS (ZARYA)"]

elif args.afsk:

   satList = ["PCSAT (NO-44)", "ISS (ZARYA)"]




#  Define The Tracker

tracker = satTracker.SatTracker()

#  Set The Ground Stations Latitude & Longitude

if args.latitude and args.longitude:
   tracker.lat = args.latitude
   tracker.lon = args.longitude


# Set Minimum Elevation For Prediction (default: 15)

if args.elevation:
   tracker.minElevation = int(args.elevation)

   
# Return Sat Pass Information

dats = tracker.satPasses(satList)
datsLen = len(dats)

# Track The Sats
client=None

try:

   while 1:

      for sat in sorted(dats, key=lambda k: k["startPass"]):
         tracker.satName = sat["satName"]
         tracker.tracker(client, sat["startPass"], sat["maxEle"], sat["endPass"])
   

      if datsLen == 0:
         print("Updating TLE Files")
         dats = tracker.satPasses(satList)


         if datsLen == 0:
            print("No Passes Found")
            break
            

except KeyboardInterrupt:
   pass