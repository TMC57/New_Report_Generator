from MyTime import date_milli

def body_total_qty_report(**kwargs):
    api_key = "eyJhbGciOiJIUzI1NiJ9.eyJmcm9tRGF0ZSI6MTc1MTg5NzQ3MTI2MywibW9kZWwiOiJwYXJ0eSIsImlkIjo0MzUwfQ.XDDPirczrQmymN3nXIwPb03JlipsNUXo_jbR053fqaQ"
    headers = {
            "Authorization" : f"Bearer {api_key}"
        }
    
    params = {
            #"limit": 1,
            "pageNumber": 1,
            "pageSize": 5,
            "fromDate": date_milli(kwargs["from_date"], "%Y-%m-%d"),
            "thruDate": date_milli(kwargs["to_date"], "%Y-%m-%d"),
            "reportType": "total-qty-facility", 
            "facilityId": 32015,      # optionnel
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