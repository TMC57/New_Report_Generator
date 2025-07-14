import requests

def model(endpoint, headers, params):
    base_url = "https://app.cm2w.net/cm2w-api/v2/api-key-auth"
    url = base_url + endpoint

    # response = requests.get(url, headers=headers, params=params)

    return(requests.get(url, headers=headers, params=params))