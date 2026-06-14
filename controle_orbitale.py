from cmath import sqrt
import math

from scipy import constants
from dataclasses import dataclass

from sgp4.api import Satrec, jday
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

@dataclass(frozen=True)
class OrbitalParameters:
    Radius1 : float
    Radius2 : float
    DeltaInclination : float


MASS_EARTH = 5.9722e24

Line1 = "1 22675U 93036A   26164.20302990  .00000068  00000+0  34083-4 0  9992"
Line2 = "2 22675  74.0398 342.4910 0024432  20.6073 339.6058 14.33255400723879"


def SatelliteCoordinates(Line1, Line2):

    Satellite = Satrec.twoline2rv(Line1, Line2)

    CrtTime = datetime.now(ZoneInfo("America/New_York"))

    JulianDay, JulianFraction = jday(CrtTime.year, CrtTime.month, CrtTime.day,
                                     CrtTime.hour, CrtTime.minute,
                                     CrtTime.second + CrtTime.microsecond)

    print("CrtTime = ", CrtTime)
    print("Julian Day = ", JulianDay)
    print("Julian Fraction = ", JulianFraction)

    #Retrieve position information
    Error,Position, Velocity = Satellite.sgp4(JulianDay, JulianFraction)

    print("Error = ", Error)
    print("Position = ", Position)
    print("Velocity = ", Velocity)


def R1R2TransferTime(r1,r2):

    Tx = constants.pi * sqrt(pow((r1 + r2),3)/(8 * constants.gravitational_constant * MASS_EARTH))
    return Tx

def InclinationChange(InclChange,VelAtOrbit):

    DelVplane = 2 * VelAtOrbit * math.sin((math.radians(InclChange))/2)

    print("DelVplane = ", DelVplane)





def OrbitTransfer(r1,r2, InclinationChange):

    #Todo: DelV1 & DelV2 to be converted to dictionary

    DelV1 = sqrt((constants.gravitational_constant * MASS_EARTH)) * (sqrt((2 * r2)/(r1 + r2)) - 1)

    DelV2 = sqrt((constants.gravitational_constant * MASS_EARTH)) * (1 - sqrt((2 * r2)/(r1 + r2)))

    print("DelV1 = ", DelV1)
    print("DelV2 = ", DelV2)

    print("Transfer Time", R1R2TransferTime(r1,r2))

    # As per reference, it is easy to perform inclination change when performing orbit tx

    if(InclinationChange > 0.0):
        InclinationChange(InclinationChange, VelAtOrbit)

    return DelV1




if __name__ == '__main__':

    print("EarthMass :", MASS_EARTH)


    Manuver1 = OrbitalParameters(Radius1 = 300000,Radius2 = 700000,DeltaInclination = 0)

    print(" DelV1 = ", OrbitTransfer(Manuver1.Radius1, Manuver1.Radius2,Manuver1.DeltaInclination))

    SatelliteCoordinates(Line1,Line2)