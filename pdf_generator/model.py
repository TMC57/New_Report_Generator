import requests
from MyTime import date_tsd

def body_total_qty_report(from_date, to_date, facility_id=None):
    api_key = "eyJhbGciOiJIUzI1NiJ9.eyJmcm9tRGF0ZSI6MTc1NjI4NDQ4MzkxNSwibW9kZWwiOiJwYXJ0eSIsImlkIjo0MzUwfQ.MHOogWqC84PZOBDvl-KlASj07Ly-CuyqBbcIj8KFmsc"
    headers = {
            "Authorization" : f"Bearer {api_key}"
        }
    
    params = {
            #"limit": 1,
            "pageNumber": 1,
            "pageSize": 1000000000,
            "fromDate": date_tsd(from_date, "%Y-%m-%d"),
            "thruDate": date_tsd(to_date, "%Y-%m-%d"),
            "reportType": "total-qty-facility", 
            "facilityId": None,      # optionnel
            # "deviceId": 456         # optionnel
        }
    if facility_id is not None:
        params["facilityId"] = facility_id
    
    endpoint = "/total-qty-report"

    return(
        endpoint,
        headers,
        params
    )


def body_devices_list(facility_id=None):
    api_key = "eyJhbGciOiJIUzI1NiJ9.eyJmcm9tRGF0ZSI6MTc1NjI4NDQ4MzkxNSwibW9kZWwiOiJwYXJ0eSIsImlkIjo0MzUwfQ.MHOogWqC84PZOBDvl-KlASj07Ly-CuyqBbcIj8KFmsc"
    headers = {
            "Authorization" : f"Bearer {api_key}"
        }
    
    params = {
            "facilityId": None      # optionnel
        }
    if facility_id is not None:
        params["facilityId"] = facility_id
    
    endpoint = "/installation-sites/devices"

    return(
        endpoint,
        headers,    
        params
    )


def body_stock_levels(facility_id=None):
    api_key = "eyJhbGciOiJIUzI1NiJ9.eyJmcm9tRGF0ZSI6MTc1NjI4NDQ4MzkxNSwibW9kZWwiOiJwYXJ0eSIsImlkIjo0MzUwfQ.MHOogWqC84PZOBDvl-KlASj07Ly-CuyqBbcIj8KFmsc"
    headers = {
            "Authorization" : f"Bearer {api_key}"
        }
    
    params = {
            "facilityId": None      # optionnel
        }
    if facility_id is not None:
        params["facilityId"] = facility_id
    
    endpoint = "/installation-sites/stocks"

    return(
        endpoint,
        headers,    
        params
    )  


def model(endpoint, headers, params):
    base_url = "https://app.cm2w.net/cm2w-api/v2/api-key-auth"
    url = base_url + endpoint
    return(requests.get(url, headers=headers, params=params))