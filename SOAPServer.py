# -*- coding: utf-8 -*-

# ladon-3.7-ctl testserve SOAPServer.py -p 8080 <-- to run
from ladon.ladonizer import ladonize
from math import sin, cos, sqrt, atan2, radians

class Calculator(object):

        @ladonize(int,int,rtype=int)
        def add(self,a,b):
                return a+b
            
class Distance(object):
        @ladonize(float,float,float,float,rtype=float)
        def calcul(self,lat1,lat2,long1,long2):
            # approximate radius of earth in km
            R = 6373.0

            lat1 = radians(lat1)
            lon1 = radians(long1)

            lat2 = radians(lat2)
            lon2 = radians(long2)

            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            distance = R * c

            return distance