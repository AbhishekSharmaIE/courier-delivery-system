"""Simple geocoding for Ireland addresses and EIRCODEs"""
import re

# Approximate coordinates for major Irish cities/regions
IRELAND_COORDINATES = {
    # Dublin area (Dublin EIRCODEs start with D)
    'dublin': (53.3498, -6.2603),
    'd01': (53.3498, -6.2603),  # Dublin 1
    'd02': (53.3396, -6.2603),  # Dublin 2
    'd03': (53.3574, -6.2603),  # Dublin 3
    'd04': (53.3300, -6.2603),  # Dublin 4
    'd05': (53.3800, -6.2603),  # Dublin 5
    'd06': (53.3300, -6.2800),  # Dublin 6
    'd07': (53.3600, -6.2800),  # Dublin 7
    'd08': (53.3400, -6.3000),  # Dublin 8
    'd09': (53.3800, -6.3000),  # Dublin 9
    'd10': (53.4000, -6.2603),  # Dublin 10
    'd11': (53.3800, -6.2400),  # Dublin 11
    'd12': (53.3400, -6.2400),  # Dublin 12
    'd13': (53.4000, -6.2400),  # Dublin 13
    'd14': (53.3200, -6.2400),  # Dublin 14
    'd15': (53.3800, -6.2200),  # Dublin 15
    'd16': (53.3200, -6.2200),  # Dublin 16
    'd17': (53.3600, -6.2000),  # Dublin 17
    'd18': (53.3000, -6.2000),  # Dublin 18
    'd20': (53.4000, -6.2000),  # Dublin 20
    'd22': (53.3400, -6.1800),  # Dublin 22
    'd24': (53.3600, -6.1600),  # Dublin 24
    
    # Cork (Cork EIRCODEs start with T or P)
    'cork': (51.8985, -8.4756),
    't12': (51.8985, -8.4756),
    't23': (51.8985, -8.4756),
    
    # Limerick (Limerick EIRCODEs start with V)
    'limerick': (52.6638, -8.6267),
    'v94': (52.6638, -8.6267),
    'v85': (52.6638, -8.6267),
    
    # Galway (Galway EIRCODEs start with H)
    'galway': (53.2707, -9.0568),
    'h91': (53.2707, -9.0568),
    
    # Waterford (Waterford EIRCODEs start with X)
    'waterford': (52.2593, -7.1100),
    'x91': (52.2593, -7.1100),
    
    # Default Ireland center
    'default': (53.4129, -8.2439),
}

def extract_eircode(address):
    """Extract EIRCODE from address string"""
    if not address:
        return None
    
    # EIRCODE format: Letter + 2 digits + space + 4 characters (e.g., D02 AF30)
    eircode_pattern = r'([A-Z]\d{2})\s*([A-Z0-9]{4})'
    match = re.search(eircode_pattern, address.upper())
    
    if match:
        return match.group(1).lower()  # Return first part (e.g., 'd02')
    
    # Also check for just the area code (e.g., "Dublin 2" or "D02")
    area_pattern = r'([A-Z]\d{1,2})'
    match = re.search(area_pattern, address.upper())
    if match:
        code = match.group(1).lower()
        if len(code) == 2:
            code = code + '0'  # Convert "D2" to "D02"
        return code
    
    return None

def geocode_ireland_address(address):
    """
    Convert Irish address or EIRCODE to approximate coordinates
    Returns (lat, lon) tuple
    """
    if not address:
        return IRELAND_COORDINATES['default']
    
    address_lower = address.lower()
    
    # Try to extract EIRCODE
    eircode = extract_eircode(address)
    if eircode and eircode in IRELAND_COORDINATES:
        # Add small random variation for different addresses in same area
        import random
        base_lat, base_lon = IRELAND_COORDINATES[eircode]
        lat = base_lat + random.uniform(-0.01, 0.01)
        lon = base_lon + random.uniform(-0.01, 0.01)
        return (lat, lon)
    
    # Check for city names
    for city, coords in IRELAND_COORDINATES.items():
        if city in address_lower and city != 'default':
            import random
            base_lat, base_lon = coords
            lat = base_lat + random.uniform(-0.02, 0.02)
            lon = base_lon + random.uniform(-0.02, 0.02)
            return (lat, lon)
    
    # Default to Dublin area if no match
    import random
    base_lat, base_lon = IRELAND_COORDINATES['dublin']
    lat = base_lat + random.uniform(-0.05, 0.05)
    lon = base_lon + random.uniform(-0.05, 0.05)
    return (lat, lon)

