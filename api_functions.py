#from botocore.vendored import requests
import requests
import json
import os
import re
from contalink_integration import get_automatic_assign

def get_pending_deals(next_start):
    try:
        full_url = (
            os.environ['PIPE_URL']
            + "deals?start="
            + str(next_start)
            + "&api_token="
            + os.environ['PIPE_TOKEN']
            + "&limit=5"
        )
        r = requests.get(full_url, headers={})
        response = json.loads(r.text)
        return response
    except Exception as e:
        print(e)
        print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE")
        return None

def iterate_deals(deals, dealCount):
    print ("START")
    results = []
    result = {}
    for deal in deals:
        print ("item")
        """
        para cada deal pendiente de asignar 
        obtener el valor de la asignacion automatica
        y asignarlo mediante el api
        try:
        full_url = (
        os.environ['PIPE_URL']
        + "deals/" + deal.id +
        + "?api_token="
        + os.environ['PIPE_TOKEN']
        )
        r = requests.put(full_url, headers={})
        results.append(json.loads(r.text))

        except Exception as e:
        print(e)
        print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE")        
        """
        result["results"] = results
        dealCount = dealCount + 1
        result["dealCount"] = dealCount
    return result
