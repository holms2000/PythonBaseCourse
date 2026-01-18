"""
    The program allows users to find a location by zip code, 
    find a zip code by city and state, 
    and determine the distance between two points specified by their zip codes.
    holms2000
"""

import math

def read_zip_all(filename):
    '''
    @requires: filename ϵ string
    @modifies: None
    @effects: None
    @raises: None
    @returns: return zip_codes from file
    '''
    i = 0
    header = []
    zip_codes = []
    zip_data = []
    skip_line = False
    # http://notebook.gaslampmedia.com/wp-content/uploads/2013/08/zip_codes_states.csv
    for line in open(filename).read().split("\n"):
        skip_line = False
        m = line.strip().replace('"', '').split(",")
        i += 1
        if i == 1:
            for val in m:
                header.append(val)
        else:
            zip_data = []
            for idx in range(0, len(m)):
                if m[idx] == '':
                    skip_line = True
                    break
                if header[idx] == "latitude" or header[idx] == "longitude":
                    val = float(m[idx])
                else:
                    val = m[idx]
                zip_data.append(val)
            if not skip_line:
                zip_codes.append(zip_data)
    return zip_codes

def decimal_to_dms(decimal_value):
    '''
    @requires: decimal_value ϵ [0,10000] 
    @modifies: None
    @effects: None
    @raises: None
    @returns: return Converts decimal latitude/longitude values ​​to degrees, minutes, and seconds (DMS).
    Direction is determined by signs: N/S for latitudes and E/W for longitudes.
    '''
    degrees = int(abs(decimal_value))
    minutes = int((abs(decimal_value) - degrees) * 60)
    seconds = ((abs(decimal_value) - degrees) * 3600) % 60
    direction = 'N' if decimal_value >= 0 else 'S' if abs(decimal_value) > 90 else 'E' if decimal_value >= 0 else 'W'
    return f"{degrees:03d}°{minutes:02d}'{seconds:.2f}\"{direction}"

def find_location_by_zip(zip_code, zip_data):
    '''
    @requires: zip_code ϵ [0,50000] ,zip_data ϵ []
    @modifies: None
    @effects: None
    @raises: None
    @returns: return city, state, county, latitude, longitude to find coordinates by postal code
    '''
    for entry in zip_data:
        if entry[0] == zip_code:
            return {
                "city": entry[3],
                "state": entry[4],
                "county": entry[5],
                "latitude": entry[1],
                "longitude": entry[2]
            }
    return None

def find_zips_by_city_state(city, state, zip_data):
    '''
    @requires: fcity, state ϵ string ,zip_data ϵ []  
    @modifies: None
    @effects: None
    @raises: None
    @returns: return zips to find zip codes by city and state from zip_data  
    '''
    zips = []
    for entry in zip_data:
        if entry[3].lower() == city.lower() and entry[4].lower() == state.lower():
            zips.append(entry[0])
    return zips

def calculate_distance(lat1, lon1, lat2, lon2):
    '''
    @requires: lat1, lon1, lat2, lon2 ϵ [-90.000,90.000]
    @modifies: None
    @effects: None
    @raises: None
    @returns: return round(distance_miles, 2) distances between two points by coordinates
    '''
    # Преобразуем градусы в радианы
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))

    # Разность углов
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    # Формула Haversine
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Средний радиус Земли в километрах
    radius_earth_km = 6371  # среднее значение радиуса Земли в километрах
    distance_km = radius_earth_km * c

    # Перевод километров в мили
    distance_miles = distance_km * 0.621371
    return round(distance_miles, 2)

def main():
    '''
    @requires: None 
    @modifies: None
    @effects: None
    @raises: None
    @returns: None
    '''
    filename = "zip_codes_states.csv"
    zip_codes = read_zip_all(filename)
    #print(zip_codes[0])
    #print(zip_codes[4108])
    
    while True:
        print("Command ('loc', 'zip', 'dist', 'end') => ")
        command = input().strip().lower()
        
        if command == 'loc':
            zip_code = input("Enter a ZIP Code to lookup => ").strip()
            location = find_location_by_zip(zip_code, zip_codes)
            
            if location:
                print(f"{zip_code}\nZIP Code {zip_code} is in {location['city']}, {location['state']}, "
                      f"{location['county']} county,\ncoordinates: ({decimal_to_dms(float(location['latitude']))}, {decimal_to_dms(float(location['longitude']))})")
            else:
                print("Invalid or unknown ZIP code")
                
        elif command == 'zip':
            city = input("Enter a city name to lookup => ").strip()
            state = input("Enter the state name to lookup => ").strip()
            zips = find_zips_by_city_state(city, state, zip_codes)
            
            if zips:
                print(f"The following ZIP Code(s) found for {city}, {state}: {', '.join(zips)}")
            else:
                print("City and/or state not found")
                
        elif command == 'dist':
            zip1 = input("Enter the first ZIP Code => ").strip()
            zip2 = input("Enter the second ZIP Code => ").strip()
            
            loc1 = find_location_by_zip(zip1, zip_codes)
            loc2 = find_location_by_zip(zip2, zip_codes)
            
            if loc1 and loc2:
                distance = calculate_distance(loc1["latitude"], loc1["longitude"], loc2["latitude"], loc2["longitude"])
                print(f"The distance between {zip1} and {zip2} is {distance} miles")
            else:
                print("One or both ZIP codes are invalid or unknown")
                
        elif command == 'end':
            print("Done")
            break
            
        else:
            print("Invalid command, ignoring")

if __name__ == "__main__":
    main()
    # del zip_codes[3]
    # zip_codes[4108][3] = 'troy'
    # zip_codes[456][1] = None
    # zip_codes[1345][2] = 0.0
    '''
    assert len(zip_codes) == 42049, \
        f'The number of ZIP codes read is {len(zip_codes)} instead of 42049'
    print(zip_codes[4108])
    assert zip_codes[4108] == \
        ['12180', 42.673701, -73.608792, 'Troy', 'NY', 'Rensselaer'], \
        'Properties of ZIP 12180 are incorrect'
    print(zip_codes[42048])
    assert zip_codes[42048] == \
        ['99950', 55.542007, -131.432682, 'Ketchikan', 'AK', 'Ketchikan Gateway'], \
        'Properties of ZIP 99950 are incorrect'
    for elem in zip_codes:
        assert elem[1] is not None and elem[1] != 0.0, \
            f'Latitude of ZIP {elem[0]} is {elem[1]} which is invalid'
        assert elem[2] is not None and elem[2] != 0.0, \
            f'Latitude of ZIP {elem[0]} is {elem[2]} which is invalid'
    print('All tests passed!')
    '''