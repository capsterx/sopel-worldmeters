import re

us = re.compile(r"^\d{5}(-{0,1}\d{4})?$")
ca = re.compile(r"([ABCEGHJKLMNPRSTVXY]\d)([ABCEGHJKLMNPRSTVWXYZ]\d){2}", re.IGNORECASE)

geolite_citydb = '_geoip_geolite2/GeoLite2-City.mmdb'

def unix_to_localtime(t, tz="US/Eastern", fmt="%H:%M:%S"):
    """
    Convert unix timestamp to local time.
    """

    from datetime import datetime
    from pytz import timezone
    import pytz

    utc = pytz.utc
    tz = timezone(tz)

    timestamp = datetime.utcfromtimestamp(t)

    return(utc.localize(timestamp).astimezone(tz).strftime(fmt))

def postal_code(string):
    """
    Check for United States and Canadian postal codes
    """

    if us.match(string):
        return "USA"
    elif ca.match(string):
        return "CAN"
    else:
        return None

def geoip_lookup(string):
    """
    Lookup the location of an IP address.
    """

    result = None

    import geoip2.database
    import sys

    from os import path

    reader = None

    for p in sys.path:
        mmdb_path = path.join(p, geolite_citydb)
        if path.exists(mmdb_path):
            reader = geoip2.database.Reader(mmdb_path)

    if not reader:
        raise Exception("Unable to locate geoip database")

    result = reader.city(string)

    return(result)
