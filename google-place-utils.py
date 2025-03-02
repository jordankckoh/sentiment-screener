import re
import requests
from urllib.parse import urlparse, parse_qs

def extract_place_id_from_url(maps_url):
    """
    Extract the place ID from various formats of Google Maps URLs
    
    Args:
        maps_url (str): Google Maps URL for a place
        
    Returns:
        str or None: The place ID if found, None otherwise
    """
    # Common URL patterns for Google Maps
    patterns = [
        # Standard place URL format
        r"place/[^/]+/([^/]+)",
        # URL with place_id parameter
        r"place_id=([^&]+)",
        # Maps URL with CID parameter
        r"maps\?.*?cid=(\d+)",
        # Maps URL with query parameter that might contain place ID
        r"maps/search/[^/@]+/@[^/]+/([^/]+)"
    ]
    
    # Try each pattern
    for pattern in patterns:
        match = re.search(pattern, maps_url)
        if match:
            return match.group(1)
    
    # If no pattern matched, try to parse URL parameters
    parsed_url = urlparse(maps_url)
    query_params = parse_qs(parsed_url.query)
    
    # Check for place_id in query parameters
    if 'place_id' in query_params:
        return query_params['place_id'][0]
    
    # Check for pbid in query parameters (sometimes used)
    if 'pbid' in query_params:
        return query_params['pbid'][0]
        
    return None

def get_location_details_from_place_id(place_id, api_key):
    """
    Get location details using the Places API
    
    Args:
        place_id (str): Google Place ID
        api_key (str): Google Places API key
        
    Returns:
        dict: Location details
    """
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,reviews,formatted_address&key={AIzaSyATw_I-Qfk2jF3rW-qhr5Er9KQ67PjocGo}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') == 'OK':
            return data.get('result', {})
        else:
            return {"error": data.get('status', 'Unknown error')}
    except Exception as e:
        return {"error": str(e)}

def convert_google_maps_url_to_embedded(maps_url):
    """
    Convert a regular Google Maps URL to an embeddable URL
    
    Args:
        maps_url (str): Regular Google Maps URL
        
    Returns:
        str: Embeddable URL
    """
    # Extract place ID
    place_id = extract_place_id_from_url(maps_url)
    
    if place_id:
        return f"https://www.google.com/maps/embed/v1/place?q=place_id:{place_id}&key=YOUR_API_KEY"
    
    # Fallback: try to create a simple embed URL from the original
    parsed_url = urlparse(maps_url)
    if 'maps.google.com' in parsed_url.netloc or 'google.com/maps' in parsed_url.netloc:
        # Replace /maps/ with /maps/embed/ if needed
        if '/maps/' in maps_url and '/maps/embed/' not in maps_url:
            return maps_url.replace('/maps/', '/maps/embed/')
    
    return None
