import requests
from MyTime import date_tsd

def body_total_qty_report(**kwargs):
    api_key = "eyJhbGciOiJIUzI1NiJ9.eyJmcm9tRGF0ZSI6MTc1MTg5NzQ3MTI2MywibW9kZWwiOiJwYXJ0eSIsImlkIjo0MzUwfQ.XDDPirczrQmymN3nXIwPb03JlipsNUXo_jbR053fqaQ"
    headers = {
            "Authorization" : f"Bearer {api_key}"
        }
    
    params = {
            #"limit": 1,
            "pageNumber": 1,
            "pageSize": 2,
            "fromDate": date_tsd(kwargs["from_date"], "%Y-%m-%d"),
            "thruDate": date_tsd(kwargs["to_date"], "%Y-%m-%d"),
            "reportType": "total-qty-facility", 
            #"facilityId": 27240,      # optionnel
            # "deviceId": 456         # optionnel
        }
    endpoint = "/total-qty-report"

    # print("voici les dates")
    # print(kwargs["from_date"])
    # print(kwargs["to_date"])

    return(
        endpoint,
        headers,
        params
    )   

def model(endpoint, headers, params):
    base_url = "https://app.cm2w.net/cm2w-api/v2/api-key-auth"
    url = base_url + endpoint

    # response = requests.get(url, headers=headers, params=params)

    return(requests.get(url, headers=headers, params=params))