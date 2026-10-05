import boto3
import json
#from botocore.vendored import requests
import requests
import traceback
import os
import re
from contalink_integration import set_va_deal_record_deal_id, get_automatic_assign, get_automatic_va_assign, get_all_pending_deals, set_assign_deal_to_true, set_va_deal_to_true, send_template_hilo, get_all_va_deals, set_auxiliar_agent, unset_auxiliar_in_deal
from api_functions import get_pending_deals, iterate_deals
from contalink_integration import get_automatic_assign_python

def send_with_ses(subject, body, from_email, recipient):
    try:
        client = boto3.client('ses')
        response = client.send_email(
        Destination={
            'ToAddresses': [
                recipient
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Data': body,
                }
            },
            'Subject': {
                'Data': subject,
            },
        },
        Source=from_email
    )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])

def get_deal_info(deal_id):
    print("Get deal info before assign.")
    deal_url = (
        os.environ['PIPE_URL']
        + "deals/" + str(deal_id)
        + "?api_token="
        + os.environ['PIPE_TOKEN']
    )
    headers = {
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
    }
    r = requests.request("GET", deal_url, headers=headers)
    result = json.loads(r.text)
    print(result)
    if result['success']:
        return result
    else:
        return None

def utms_from_person(deal_id):
    print("UTMS FROM PERSON")
    first_visit_date = None
    first_utm = None
    utm_campaign = None
    utm_medium = None
    utm_source = None
    person_id = None
    lead_type = None
    # Obtener Deal
    deal_url = (
        os.environ['PIPE_URL']
        + "deals/" + str(deal_id)
        + "?api_token="
        + os.environ['PIPE_TOKEN']
    )
    headers = {
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
    }
    r = requests.request("GET", deal_url, headers=headers)
    result = json.loads(r.text)
    print(result)
    if result['success']:
        person_id = result['data']['person_id']['value']
        first_visit_date = result['data']['1fba77d95708dcb09f4be2adc40275eeb3479138']
        first_utm = result['data']['448a0af69a24744b729ba2c494bb172609cf30f3']
        utm_campaign = result['data']['1ec1628154aca7d01b14638424caabfdc83834ea']
        utm_medium = result['data']['39f425f87fc043b3a7a82419cd11aa3187837eb8']
        utm_source = result['data']['1b2aa66ccef5fa6bc8a7ac45172cd8849fb16d21']
        person_url = (
            os.environ['PIPE_URL']
            + "persons/" + str(person_id)
            + "?api_token="
            + os.environ['PIPE_TOKEN']
        )
        headers = {
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
        }
        r = requests.request("GET", person_url, headers=headers)
        person = json.loads(r.text)
        print(person)
        if person['success']:


            invalid_values = ('', 'Desconocido', None)
            if first_visit_date in invalid_values:
                if person['data']['50b21fe54d4a46e534376e79f8dc619454bb9197'] not in invalid_values:
                    first_visit_date = person['data']['50b21fe54d4a46e534376e79f8dc619454bb9197']

            if first_utm in invalid_values:
                if person['data']['df47d17426e7e942f6f1d8d929dc403444888323'] not in invalid_values:
                    first_utm = person['data']['df47d17426e7e942f6f1d8d929dc403444888323']

            if utm_campaign in invalid_values:
                if person['data']['8e80ba8b81f1da1a89da2068fc2789a3cebacfec'] not in invalid_values:
                    utm_campaign = person['data']['8e80ba8b81f1da1a89da2068fc2789a3cebacfec']

            if utm_medium in invalid_values:
                if person['data']['942b243e497ed1527d91d1b665886eed39970a29'] not in invalid_values:
                    utm_medium = person['data']['942b243e497ed1527d91d1b665886eed39970a29']

            if utm_source in invalid_values:
                if person['data']['458e2ef783582e5fb8732b4450d7903cecae7809'] not in invalid_values:
                    utm_source = person['data']['458e2ef783582e5fb8732b4450d7903cecae7809']

            if 'f127ae2b9a5c39fb528f0933f862cb5e3dcefe70' in person['data']:
                if person['data']['f127ae2b9a5c39fb528f0933f862cb5e3dcefe70'] == '531':
                    lead_type = '347'

            # Actualizar deal:
            full_url = (
                os.environ['PIPE_URL']
                + "deals/" + deal_id
                + "?api_token="
                + os.environ['PIPE_TOKEN']
            )
            
            updatePayload = {
                "1fba77d95708dcb09f4be2adc40275eeb3479138": first_visit_date,
                "448a0af69a24744b729ba2c494bb172609cf30f3": first_utm,
                "1ec1628154aca7d01b14638424caabfdc83834ea": utm_campaign,
                "39f425f87fc043b3a7a82419cd11aa3187837eb8": utm_medium,
                "1b2aa66ccef5fa6bc8a7ac45172cd8849fb16d21": utm_source
            }

            if lead_type is not None:
                updatePayload["3098fab920387ade3b098c60b1230bdb516723d8"] = lead_type

            updateBody = json.dumps(updatePayload)

            headers = {
                'Content-Type': 'application/json',
                'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
            }
            r = requests.request("PUT", full_url, headers=headers, data=updateBody)
            print("result: ")
            print (json.loads(r.text))

def isPipeDriveLite(person_id, person_two_id):
    # Valida si cualquiera de las dos personas involucradas son lite.
    print("Es persona lite?")
    print(person_id)
    person_url = (
        os.environ['PIPE_URL']
        + "persons/" + str(person_id)
        + "?api_token="
        + os.environ['PIPE_TOKEN']
    )
    headers = {
    'Content-Type': 'application/json',
    'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
    }
    r = requests.request("GET", person_url, headers=headers)
    result = json.loads(r.text)
    print(result)
    if result['success']:
        if result['data']['1d39947e099d9142d9eb0b0b55ab54ffab866423'] == '485':
            return True
    print("Es persona 2 lite?")
    print(person_two_id)
    person_url = (
        os.environ['PIPE_URL']
        + "persons/" + str(person_two_id)
        + "?api_token="
        + os.environ['PIPE_TOKEN']
    )
    headers = {
    'Content-Type': 'application/json',
    'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
    }
    r = requests.request("GET", person_url, headers=headers)
    result = json.loads(r.text)
    print(result)
    if result['success']:
        if result['data']['1d39947e099d9142d9eb0b0b55ab54ffab866423'] == '485':
            return True            
    print("No es persona 2 Lite")
    return False

def merge_va_deals(environment):
    print("Merging VA Deals")
    print("START")
    print("environment:")
    print(environment)
    print(":::::::::::")
    response = {}
    results = []
    merge_results = []
    merge_deal_results = []
    timbrada = False
    allOk = True
    Message = "Asignado: ";
    try:
        
        params = None
        print("GLORIA")
        os.environ['PIPE_URL'] = "https://contalink.pipedrive.com/api/v1/"
        #os.environ['PIPE_TOKEN'] = "134bde7bf737a397258c8b463194e808e4fe1ad5" # Gloria
        os.environ['PIPE_TOKEN'] = "0265cdd4911c8d00da7b508d60ec5171fa4b5e00" # Tecnología
        os.environ['SMS_URL'] = 'https://fel92muvy4.execute-api.us-east-1.amazonaws.com/prod/cl-send-sms/pinpoint'
        os.environ['SMS_API_KEY'] = '0cpC9DfinI6ZgblN6GBEY3O4pJ1FK4pz4a9r0dfI'
        os.environ['FROM_PHONE'] = '+18447501370'

        has_more = True
        contactCount = 0
        dealCount = 0
        next_start = 0
        print("get all VA deals")
        deals = get_all_va_deals(environment)
        
        for deal in deals:
            print("asignar deal: " + str(deal['deal_id']))
            automatic_assign = get_automatic_va_assign(environment, deal['deal_id'])
            print("AA:")
            print(automatic_assign)
            if automatic_assign["action"] == "MERGE_VA_DEALS":
                # agregar el deal actual a la lista
                automatic_assign["va_deals"].append(deal['deal_id'])
                # Eliminar duplicados
                automatic_assign["va_deals"] = list(set(automatic_assign["va_deals"]))
                # Ordenar
                automatic_assign["va_deals"] = sorted(automatic_assign["va_deals"])
                # obtener el último elemento de la lista, el más nuevo
                va_last_deal = automatic_assign["va_deals"].pop()
                print("Lista Deals")
                print(automatic_assign["va_deals"])
                print("Último Deal")
                print(va_last_deal)
                # si en la lista va_last_deal queda un sólo deal y es ganado
                # el ganado es el que debe prevalecer
                if len(automatic_assign["va_deals"]) == 1:
                    if automatic_assign["va_deals"][0] == automatic_assign["va_won_deal_id"]:
                        automatic_assign["va_deals"][0] = va_last_deal
                        va_last_deal = automatic_assign["va_won_deal_id"]
                type_lead_priority = get_type_lead_priority(str(va_last_deal), automatic_assign["va_deals"]) # 280526    
                # recorrer del más viejo al más nuevo
                for va_deal in automatic_assign["va_deals"]:
                    # mergear con todos menos consigo mismo, con deals ganados ni con deals mayores
                    try:
                        merge_deal_url = (
                            os.environ['PIPE_URL']
                            + "deals/" +  str(va_deal)
                            + "/merge?api_token="
                            + os.environ['PIPE_TOKEN']
                        )
                        mergeDealBody = json.dumps({
                            "merge_with_id": str(va_last_deal)
                        })
                        headers = {
                            'Content-Type': 'application/json',
                            'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                        }
                        r = requests.request("PUT", merge_deal_url, headers=headers, data=mergeDealBody)
                        print("result: ")
                        print (json.loads(r.text))
                        merge_deal_result = json.loads(r.text)                            
                        if merge_deal_result['success'] == True:
                            update = set_va_deal_to_true(environment, deal['deal_id'])
                            print("MERGEADO -- " + str(va_deal) + " a " + str(va_last_deal) + " este último prevalece.")
                        else:
                            print("Merge Error!")
                    except Exception as e:
                        print("merge deal exception")
                        print(e)
                        print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE W")
                if type_lead_priority["update"]:    # 280526
                        update_type_lead_priority(type_lead_priority["type_lead"], str(va_last_deal)) # 280526                        
                
            elif automatic_assign["action"] == "MERGE_2ND_PHASE":
                # Mergear y prevalecer Inbound
                print("Merge 2nd Phase")
                type_lead_priority = get_type_lead_priority( str(deal['deal_id']), [str(automatic_assign["merge_deal_id"])]) # 280526
                try:
                    merge_deal_url = (
                        os.environ['PIPE_URL'] 
                        + "deals/" + str(automatic_assign["merge_deal_id"]) 
                        + "/merge?api_token="
                        + os.environ['PIPE_TOKEN'] 
                    )
                    mergeDealBody = json.dumps({
                        "merge_with_id":  str(deal['deal_id'])
                    })
                    headers = {
                      'Content-Type': 'application/json',
                      'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                    }
                    # 
                    r = requests.request("PUT", merge_deal_url, headers=headers, data=mergeDealBody)
                    print("result: ")
                    print (json.loads(r.text))
                    merge_deal_result = json.loads(r.text)                            
                    if merge_deal_result['success'] == True:
                        update = set_va_deal_to_true(environment, deal['deal_id'])
                        print("MERGEADO -- " +str(automatic_assign["merge_deal_id"]) + " a " +  str(deal['deal_id']) + " este último prevalece.")
                        # Cambiar titulo y asígnación de deal abierto.

                        ##############################################################
                        full_url = (
                            os.environ['PIPE_URL']
                            + "deals/" + str(deal['deal_id'])
                            + "?api_token="
                            + os.environ['PIPE_TOKEN']
                        )
                        #Gloria: 5995501 | Hiram: 11607065
                        # TODO cuando cambie a CRON
                        # el 11607065 pasa a automatic_assign_id

                        

                        payload_dict = {
                            "title": automatic_assign["title_open_deal"],
                            "user_id": automatic_assign["assign_open_deal"]
                        }
                        if type_lead_priority["update"]: # 280526
                            payload_dict["3098fab920387ade3b098c60b1230bdb516723d8"] = type_lead_priority["type_lead"]

                        updateBody = json.dumps(payload_dict)

                        headers = {
                          'Content-Type': 'application/json',
                          'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                        }
                    
                        r = requests.request("PUT", full_url, headers=headers, data=updateBody)
                        ##############################################################                        
                        
                    else:
                        print("Merge Error!")
                except Exception as e:
                    print("merge deal exception")
                    print(e)
                    print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE I")                                
            elif automatic_assign["action"] == "MERGE_1ST_PHASE":
                # Mergear y prevalecer VA
                type_lead_priority = get_type_lead_priority(str(deal['deal_id']), [str(automatic_assign["merge_deal_id"])])  # 280526
                try:
                    merge_deal_url = (
                        os.environ['PIPE_URL']
                        + "deals/" + str(automatic_assign["merge_deal_id"])
                        + "/merge?api_token="
                        + os.environ['PIPE_TOKEN']
                    )
                    mergeDealBody = json.dumps({
                        "merge_with_id": str(deal['deal_id'])
                    })
                    headers = {
                      'Content-Type': 'application/json',
                      'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                    }
                    r = requests.request("PUT", merge_deal_url, headers=headers, data=mergeDealBody)
                    print("result: ")
                    print (json.loads(r.text))
                    merge_deal_result = json.loads(r.text)                            
                    if merge_deal_result['success'] == True:
                        update = set_va_deal_to_true(environment, deal['deal_id'])
                        if type_lead_priority["update"]: #280526
                            update_type_lead_priority(type_lead_priority["type_lead"], str(deal['deal_id']))
                        print("MERGEADO -- " + str(automatic_assign["merge_deal_id"]) + " a " +  str(deal['deal_id']) + " este último prevalece.")
                    else:
                        print("Merge Error!")
                except Exception as e:
                    print("merge deal exception")
                    print(e)
                    print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE II") 
            
            # En cualquiera de los 3 casos hay que mergear contactos.
            # siempre prevalece el último contacto.
            update = set_va_deal_to_true(environment, deal['deal_id'])

            if automatic_assign["action"] == "MERGE_VA_DEALS":
                # merge especial para VA


                # agregar el persona
                automatic_assign["persons_to_merge"].append(automatic_assign["newest_person_id"])
                # Eliminar duplicados
                automatic_assign["persons_to_merge"] = list(set(automatic_assign["persons_to_merge"]))
                # Ordenar
                automatic_assign["persons_to_merge"] = sorted(automatic_assign["persons_to_merge"])
                # obtener el último elemento de la lista, el más nuevo
                va_last_person = automatic_assign["persons_to_merge"].pop()
                print("Lista Deals")
                print(automatic_assign["persons_to_merge"])
                print("Último Deal")
                print(va_last_person)
                # recorrer del más viejo al más nuevo




                if len(automatic_assign["persons_to_merge"]) <= 4:
                    # Sólo mergear menos de 3 contactos para evitar errores koala
                    for person in automatic_assign["persons_to_merge"]: 
                        try:
                            merge_url = (
                                os.environ['PIPE_URL']
                                + "persons/" + str(person)
                                + "/merge?api_token="
                                + os.environ['PIPE_TOKEN']
                            )
                            mergeBody = json.dumps({
                                "merge_with_id": str(va_last_person)
                            })
                            
                            headers = {
                            'Content-Type': 'application/json',
                            'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                            }
                        
                            r = requests.request("PUT", merge_url, headers=headers, data=mergeBody)
                            print("result: ")
                            print (json.loads(r.text))
                            merge_result = json.loads(r.text)
                            print("start merge deal")
                            if merge_result['success'] == True:
                                print("SUCCESS PERSON MERGE")
                                print("Merge " + str(person)+ " a " + str(va_last_person) + " este último prevalce.")
                            else:
                                print("Ha habido un error al mergear la persona")
                        except Exception as e:
                            print(e)
                            print("ERROR PERSON MERGE")                                    
            else:
                if automatic_assign["newest_person_id"] is not None and automatic_assign["older_person_id"] is not None:
                    print("fusionar " + str(automatic_assign["older_person_id"]) + " con " + str(automatic_assign["newest_person_id"]) + " este ultimo manda.")
                    try:
                        merge_url = (
                            os.environ['PIPE_URL']
                            + "persons/" + str(automatic_assign["older_person_id"])
                            + "/merge?api_token="
                            + os.environ['PIPE_TOKEN']
                        )
                        mergeBody = json.dumps({
                            "merge_with_id": str(automatic_assign["newest_person_id"])
                        })
                        
                        headers = {
                        'Content-Type': 'application/json',
                        'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                        }
                    
                        r = requests.request("PUT", merge_url, headers=headers, data=mergeBody)
                        print("result: ")
                        print (json.loads(r.text))
                        merge_result = json.loads(r.text)
                        print("start merge deal")
                        if merge_result['success'] == True:
                            print("SUCCESS PERSON MERGE")
                        else:
                            print("Ha habido un error al mergear la persona")
                    except Exception as e:
                        print(e)
                        print("ERROR PERSON MERGE")
                elif automatic_assign["newest_person_id"] is not None and automatic_assign["persons_to_merge"] is not None:
                    if len(automatic_assign["persons_to_merge"]) <= 3:
                        # Sólo mergear menos de 3 contactos para evitar errores koala
                        for person in automatic_assign["persons_to_merge"]: 
                            try:
                                merge_url = (
                                    os.environ['PIPE_URL']
                                    + "persons/" + str(person)
                                    + "/merge?api_token="
                                    + os.environ['PIPE_TOKEN']
                                )
                                mergeBody = json.dumps({
                                    "merge_with_id": str(automatic_assign["newest_person_id"])
                                })
                                
                                headers = {
                                'Content-Type': 'application/json',
                                'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                                }
                            
                                r = requests.request("PUT", merge_url, headers=headers, data=mergeBody)
                                print("result: ")
                                print (json.loads(r.text))
                                merge_result = json.loads(r.text)
                                print("start merge deal")
                                if merge_result['success'] == True:
                                    print("SUCCESS PERSON MERGE")
                                else:
                                    print("Ha habido un error al mergear la persona")
                            except Exception as e:
                                print(e)
                                print("ERROR PERSON MERGE")                    

            
    except Exception as ex:
        traceback.print_exc()
        response['status'] = 0
        response['message'] = str(ex)
        print(json.dumps(response))
        return response
                    
            
            


def merge_va_deals_old(environment):
    print("Merging VA Deals")
    print("START")
    print("environment:")
    print(environment)
    print(":::::::::::")
    response = {}
    results = []
    merge_results = []
    merge_deal_results = []
    timbrada = False
    allOk = True
    Message = "Asignado: ";
    try:
        
        params = None
        # TODO Cambiar para deploys
        #environment = event['body-json']['ENV'] # Lambda
        
        print("GLORIA")
        os.environ['PIPE_URL'] = "https://contalink.pipedrive.com/api/v1/"
        #os.environ['PIPE_TOKEN'] = "134bde7bf737a397258c8b463194e808e4fe1ad5" # Gloria
        os.environ['PIPE_TOKEN'] = "0265cdd4911c8d00da7b508d60ec5171fa4b5e00" # Tecnología

        os.environ['SMS_URL'] = 'https://fel92muvy4.execute-api.us-east-1.amazonaws.com/prod/cl-send-sms/pinpoint'
        os.environ['SMS_API_KEY'] = '0cpC9DfinI6ZgblN6GBEY3O4pJ1FK4pz4a9r0dfI'
        os.environ['FROM_PHONE'] = '+18447501370'

        has_more = True
        contactCount = 0
        dealCount = 0
        next_start = 0
        print("get all VA deals")
        deals = get_all_va_deals(environment)
        
        for deal in deals:
            print("asignar deal: " + str(deal['deal_id']))
            automatic_assign = get_automatic_va_assign(environment, deal['deal_id'])
            print("Auto Assign.")
            print(automatic_assign)
            automatic_assign_id = automatic_assign["user"]["id"]
            # si va a haber mergeo de deals la asignación será al oldest deal por que el deal actual 
            # desaparecerá.
            if automatic_assign["peding_deals"] == True:
                deal_to_assign = str(automatic_assign["oldest_deal"])
                # si el deal más viejo no esta en x asignar se debe mantener el asignado
            else:
                deal_to_assign = str(deal['deal_id'])
            try:
                results.append('Se ha asignado el deal ' + str(deal['deal_id']) + ' a ' + str(automatic_assign_id))
                update = set_va_deal_to_true(environment, deal['deal_id'])
                
                if automatic_assign["peding_contacts"] == True:
                    for person in automatic_assign["person_to_merge"]:
                        print("fusionar " + str(person) + " con " + str(automatic_assign["person_id"]) + " este ultimo manda.")
                        try:
                            merge_url = (
                                os.environ['PIPE_URL']
                                + "persons/" + str(person)
                                + "/merge?api_token="
                                + os.environ['PIPE_TOKEN']
                            )
                            mergeBody = json.dumps({
                                "merge_with_id": automatic_assign["person_id"]
                            })
                            
                            # Si la persona nueva es lite entonces la prioridad del mergeo la debe tener
                            # la persona más antigua 
                            if isPipeDriveLite(automatic_assign["person_id"], person):
                                print("Es persona lite cambiar la prioridad del merge")
                                merge_url = (
                                    os.environ['PIPE_URL']
                                    + "persons/" + str(automatic_assign["person_id"])
                                    + "/merge?api_token="
                                    + os.environ['PIPE_TOKEN']
                                )
                                mergeBody = json.dumps({
                                    "merge_with_id": str(person)
                                })
                            
                            
                            
                            headers = {
                              'Content-Type': 'application/json',
                              'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                            }

                            #r = requests.put(merge_url, headers={}, json=mergeBody)
                            r = requests.request("PUT", merge_url, headers=headers, data=mergeBody)
                            print("result: ")
                            print (json.loads(r.text))
                            merge_result = json.loads(r.text)
                            print("start merge deal")
                            if merge_result['success'] == True:
                                print("merge person was success")
                                #add1stActivityToVADeal(deal['deal_id'])
                                merge_results.append("fusionado " + str(person) + " con " + str(automatic_assign["person_id"]) + " este ultimo manda.")
                                update = set_va_deal_to_true(environment, deal['deal_id'])
                                print("deal status was updated")
                                # MERGE DEALS VA
                                print("Mergear DEALs")
                                if automatic_assign["peding_deals"] == True:
                                    print("respose has pending deals")
                                    for current_deal in automatic_assign["open_deals"]:
                                        print("fusionar " + str(current_deal) + " con " + str(deal['deal_id']) + " este ultimo manda.")
                                        try:
                                            merge_deal_url = (
                                                os.environ['PIPE_URL']
                                                + "deals/" +  str(current_deal)
                                                + "/merge?api_token="
                                                + os.environ['PIPE_TOKEN']
                                            )
                                            mergeDealBody = json.dumps({
                                                "merge_with_id": automatic_assign["oldest_deal"]
                                            })
                                            headers = {
                                              'Content-Type': 'application/json',
                                              'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                                            }
                                            #+ "deals/" + str(current_deal)
                                            #"merge_with_id": deal['deal_id'] # el deal que ya existía
                                            #r = requests.put(merge_deal_url, headers={}, json=mergeDealBody)
                                            r = requests.request("PUT", merge_deal_url, headers=headers, data=mergeDealBody)
                                            print("result: ")
                                            print (json.loads(r.text))
                                            merge_deal_result = json.loads(r.text)                            
                                            if merge_deal_result['success'] == True:
                                                #add1stActivityToVADeal(deal['deal_id'])
                                                merge_deal_results.append("fusionado " + str(current_deal) + " con " + str(deal['deal_id']) + " este ultimo manda.")
                                                # Despues de mergear los contactos y deals
                                                set_va_deal_record_deal_id(environment, current_deal, deal['deal_id'])
                                                utms_from_person(deal_to_assign)
                                                if automatic_assign["va_flag"] is not None:
                                                    vaActions(automatic_assign["va_flag"], automatic_assign["oldest_deal"], None)
                                            else:
                                                print("Merge Error!")
                                                merge_deal_results.append("Ha habido un error al mergear los deals")
                                        except Exception as e:
                                            print("merge deal exception")
                                            print(e)
                                            merge_deal_results.append('Merge Deal Error:' + str(e))
                                            print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE IV") 
                                else:
                                    # Despues de mergear los contactos no hubo deals
                                    utms_from_person(deal_to_assign)
                                print("end merge deals")
                                # MERGE DEAL
                            
                                
                            else:
                                print("Merge Error!")
                                merge_results.append("Ha habido un error al mergear las personas")
                        except Exception as e:
                            print(e)
                            merge_results.append('Merge Person Error:' + str(e))
                            print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE A")                                       
                else:
                    # no hay contactos por fusionar
                    if automatic_assign["peding_deals"] == True:
                        print("respose has pending deals")
                        for current_deal in automatic_assign["open_deals"]:
                            print("fusionar " + str(current_deal) + " con " + str(deal['deal_id']) + " este ultimo manda.")
                            # MERGE DEALS VA
                            try:
                                merge_deal_url = (
                                    os.environ['PIPE_URL']
                                    + "deals/" +  str(current_deal)
                                    + "/merge?api_token="
                                    + os.environ['PIPE_TOKEN']
                                )
                                mergeDealBody = json.dumps({
                                    "merge_with_id": automatic_assign["oldest_deal"]
                                })
                                headers = {
                                  'Content-Type': 'application/json',
                                  'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                                }
                                #+ "deals/" + str(current_deal)
                                #"merge_with_id": deal['deal_id'] # el deal que ya existía
                                #r = requests.put(merge_deal_url, headers={}, json=mergeDealBody)
                                r = requests.request("PUT", merge_deal_url, headers=headers, data=mergeDealBody)
                                print("result: ")
                                print (json.loads(r.text))
                                merge_deal_result = json.loads(r.text)                            
                                if merge_deal_result['success'] == True:
                                    #add1stActivityToVADeal(deal['deal_id'])
                                    merge_deal_results.append("fusionado " + str(current_deal) + " con " + str(deal['deal_id']) + " este ultimo manda.")
                                    # Despues de mergear los deals no hubo contactos
                                    set_va_deal_record_deal_id(environment, current_deal, deal['deal_id'])
                                    utms_from_person(deal_to_assign)
                                    if automatic_assign["va_flag"] is not None:
                                        vaActions(automatic_assign["va_flag"], automatic_assign["oldest_deal"], None)
                                else:
                                    print("Merge Error!")
                                    merge_deal_results.append("Ha habido un error al mergear los deals")
                            except Exception as e:
                                print("merge deal exception")
                                print(e)
                                merge_deal_results.append('Merge Deal Error:' + str(e))
                                print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE B") 
                    else:
                        #Sin deals por fusionar
                        print("No deals por fusionar")
                        # Sin contactos ni deals por fusionar
                        utms_from_person(deal_to_assign)
                    print("end merge deals")
                    # MERGE DEAL

            except Exception as e:
                print(e)
                results.append('Assign Error:' + str(e))
                print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE")               
        
        response['results'] = results
        response['merge_result'] = merge_results
        response['merge_deal_result'] = merge_deal_results
        print("=========RESPONSE=================")
        print(response)
        print("======== NOTIFICATION ============")
        
        return response

    except Exception as ex:
        traceback.print_exc()
        if timbrada == False:
            response['status'] = 0
            response['message'] = str(ex)
            print(json.dumps(response))
        return response

def lambda_handler(event, context):
    #print ('Lambra HNLR' + str(event))
    print("START LATEST")
    print("event:")
    print(event)
    print(":::::::::::")
    response = {}
    results = []
    merge_results = []
    merge_deal_results = []
    timbrada = False
    allOk = True
    Message = "Asignado: ";
    try:
        
        params = None
        # TODO Cambiar para deploys
        if 'body-json' in event:
            environment = event['body-json']['ENV'] # Lambda
            if 'VA' in event['body-json']:
                if event['body-json']['VA'] is True:
                    merge_va_deals(environment)
                    return None    
        else: 
            environment = json.loads(event['body'])["body-json"]["ENV"]
            print("VA Deals Merging")
            merge_va_deals(environment)
            return None
        #environment = event['ENV'] # Local
        print("GLORIA")
        os.environ['PIPE_URL'] = "https://contalink.pipedrive.com/api/v1/"
        #os.environ['PIPE_TOKEN'] = "e21225cc63ba68bfa2f1d5801eaa9a07f8c1e8d0" # Alex
        #os.environ['PIPE_TOKEN'] = "1f6a5c2987de01df6967b9e9f7888966aa208fa7" # Julio
        #os.environ['PIPE_TOKEN'] = "134bde7bf737a397258c8b463194e808e4fe1ad5" # Gloria
        os.environ['PIPE_TOKEN'] = "0265cdd4911c8d00da7b508d60ec5171fa4b5e00" # Tecnología
        

        os.environ['SMS_URL'] = 'https://fel92muvy4.execute-api.us-east-1.amazonaws.com/prod/cl-send-sms/pinpoint'
        os.environ['SMS_API_KEY'] = '0cpC9DfinI6ZgblN6GBEY3O4pJ1FK4pz4a9r0dfI'
        os.environ['FROM_PHONE'] = '+18447501370'

        has_more = True
        contactCount = 0
        dealCount = 0
        next_start = 0
        print("get all deals")
        deals = get_all_pending_deals(environment)

        for deal in deals:
            print("asignar deal: " + str(deal['deal_id']))
            # se agrego esta línea 29 de enero 2026 por que estaba dando problemas
            updates = set_assign_deal_to_true(environment, deal['deal_id'])


            
            #Descomentar esto cuando salgas a producción.
            #print(" + + + + A S I G N A R  A G E N T E  A U X I L I A R + + + + ")
            #auxiliar = set_auxiliar_agent(environment, deal['deal_id'])
            #print("modificar Actividad")
            #if 'next_auxiliar_agent' in auxiliar:
            #    addNoteAuxiliar(environment, auxiliar['next_auxiliar_agent'], deal['deal_id'])
            #else:
            #    print("No se pudo asignar agente, saltando actualización de actividades.")
            
            print(" + + + +  A S I G N A C I O N   A U T O M A T I C A + + + + ")
            automatic_assign = get_automatic_assign_python(
                environment,
                deal['deal_id'],
                commit=True,
                debug=True
            )
            print("asignacion piloto:" + str(automatic_assign))

            #automatic_assign = get_automatic_assign(environment, deal['deal_id'])
            automatic_assign_id = automatic_assign["user"]["id"]
            addNoteAuxiliar(environment, automatic_assign["user"]["id"], deal['deal_id'])
            print("asignacion automatica:" + str(automatic_assign))
            print("Usuario asignado:"+str(automatic_assign_id))
            print("Actualizar un deal mediante el API")
            print("OLDEST STAGE:"+str(automatic_assign["oldest_stage"]))
            # si va a haber mergeo de deals la asignación será al oldest deal por que el deal actual 
            # desaparecerá.
            if automatic_assign["peding_deals"] == True:
                deal_to_assign = str(automatic_assign["oldest_deal"])
                # si el deal más viejo no esta en x asignar se debe mantener el asignado
            else:
                deal_to_assign = str(deal['deal_id'])
            try:

                # Obtener info del deal a asignar
                deal_info = get_deal_info(deal_to_assign)
                # asignar equipo de ventas cuando el canal venga nulo
                canal_de_ventas = None
                if "c2157d1b51b616525377caf343241bf3ddfffa4a" in deal_info["data"]:
                    if deal_info["data"]["c2157d1b51b616525377caf343241bf3ddfffa4a"] is None:
                        canal_de_ventas = "428"
                    else:
                        canal_de_ventas = deal_info["data"]["c2157d1b51b616525377caf343241bf3ddfffa4a"]


                full_url = (
                    os.environ['PIPE_URL']
                    + "deals/" + deal_to_assign
                    + "?api_token="
                    + os.environ['PIPE_TOKEN']
                )
                #Gloria: 5995501 | Hiram: 11607065
                # TODO cuando cambie a CRON
                # el 11607065 pasa a automatic_assign_id
                updateBody = json.dumps({
                    "user_id": automatic_assign_id,
                    "stage_id": automatic_assign["oldest_stage"] or 250, # cuando el oldest deal es diferente 
                    "c2157d1b51b616525377caf343241bf3ddfffa4a": canal_de_ventas
                })
                headers = {
                  'Content-Type': 'application/json',
                  'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                }

                # POST Asignación
                r = requests.request("PUT", full_url, headers=headers, data=updateBody)

                print("result: ")
                print (json.loads(r.text))
                result = json.loads(r.text)
                if result['success'] == True:
                    results.append('Se ha asignado el deal ' + str(deal['deal_id']) + ' a ' + str(automatic_assign_id))
                    # Marcar deal como asignado
                    update = set_assign_deal_to_true(environment, deal['deal_id'])
                    # Notificaciones pendientes de Slack
                    #if deal_info["data"]["505f3fe31685adda13a26cf09b69995a6f27a143"] in ('TALKNOW', 'TALKHERE'):
                    if deal_info.get("data", {}).get("505f3fe31685adda13a26cf09b69995a6f27a143") in ('TALKNOW', 'TALKHERE'):  
                        slackBody = json.dumps({
                            "deal_id": deal['deal_id'],
                            "action": deal_info["data"]["505f3fe31685adda13a26cf09b69995a6f27a143"],
                            "token": os.environ['SALES_BOT_HILOS_TOKEN'],
                            "assigned": True
                        })
                        headers = {
                        'Content-Type': 'application/json',
                        'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                        }   
                        slack = requests.request("POST", os.environ['SALES_BOT_HILOS_URL'], headers=headers, data=slackBody)                 

                    # AQUI SE OBTIENE LA INFORMACION DEL DEAL PARA EL ENVIO DE LA INFORMACION
                    print('Entra al envio del flujo: ')
                    send_template_hilo(deal['deal_id'])
                    if automatic_assign["peding_contacts"] == True:
                        for person in automatic_assign["person_to_merge"]:
                            print("fusionar " + str(person) + " con " + str(automatic_assign["person_id"]) + " este ultimo manda.")
                            try:
                                merge_url = (
                                    os.environ['PIPE_URL']
                                    + "persons/" + str(person)
                                    + "/merge?api_token="
                                    + os.environ['PIPE_TOKEN']
                                )
                                mergeBody = json.dumps({
                                    "merge_with_id": automatic_assign["person_id"]
                                })
                                
                                # Si la persona nueva es lite entonces la prioridad del mergeo la debe tener
                                # la persona más antigua 
                                if isPipeDriveLite(automatic_assign["person_id"], person):
                                    print("Es persona lite cambiar la prioridad del merge")
                                    merge_url = (
                                        os.environ['PIPE_URL']
                                        + "persons/" + str(automatic_assign["person_id"])
                                        + "/merge?api_token="
                                        + os.environ['PIPE_TOKEN']
                                    )
                                    mergeBody = json.dumps({
                                        "merge_with_id": str(person)
                                    })
                                
                                
                                
                                headers = {
                                  'Content-Type': 'application/json',
                                  'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                                }

                                #r = requests.put(merge_url, headers={}, json=mergeBody)
                                r = requests.request("PUT", merge_url, headers=headers, data=mergeBody)
                                print("result: ")
                                print (json.loads(r.text))
                                merge_result = json.loads(r.text)
                                print("start merge deal")
                                if merge_result['success'] == True:
                                    print("merge person was success")
                                    merge_results.append("fusionado " + str(person) + " con " + str(automatic_assign["person_id"]) + " este ultimo manda.")
                                    update = set_assign_deal_to_true(environment, deal['deal_id'])
                                    print("deal status was updated")
                                    # MERGE DEALs
                                    print("Mergear DEALs")
                                    if automatic_assign["peding_deals"] == True:
                                        print("respose has pending deals II")
                                        type_lead_priority = get_type_lead_priority(automatic_assign["oldest_deal"], automatic_assign["open_deals"]) #280526
                                        for current_deal in automatic_assign["open_deals"]:
                                            print("fusionar " + str(current_deal) + " con " + str(deal['deal_id']) + " este ultimo manda.")

                                            try:
                                                merge_deal_url = (
                                                    os.environ['PIPE_URL']
                                                    + "deals/" +  str(current_deal)
                                                    + "/merge?api_token="
                                                    + os.environ['PIPE_TOKEN']
                                                )
                                                mergeDealBody = json.dumps({
                                                    "merge_with_id": automatic_assign["oldest_deal"]
                                                })
                                                headers = {
                                                  'Content-Type': 'application/json',
                                                  'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                                                }
                                                #+ "deals/" + str(current_deal)
                                                #"merge_with_id": deal['deal_id'] # el deal que ya existía
                                                #r = requests.put(merge_deal_url, headers={}, json=mergeDealBody)
                                                r = requests.request("PUT", merge_deal_url, headers=headers, data=mergeDealBody)
                                                print("result: ")
                                                print (json.loads(r.text))
                                                merge_deal_result = json.loads(r.text)                            
                                                if merge_deal_result['success'] == True:
                                                    merge_deal_results.append("fusionado " + str(current_deal) + " con " + str(deal['deal_id']) + " este ultimo manda.")
                                                    # Despues de mergear los contactos y deals
                                                    utms_from_person(deal_to_assign)
                                                else:
                                                    print("Merge Error!")
                                                    merge_deal_results.append("Ha habido un error al mergear los deals")
                                            except Exception as e:
                                                print("merge deal exception")
                                                print(e)
                                                merge_deal_results.append('Merge Deal Error:' + str(e))
                                                print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE C")
                                        if type_lead_priority["update"]:     #280526
                                            update_type_lead_priority(type_lead_priority["type_lead"], automatic_assign["oldest_deal"])
                                    else:
                                        # Despues de mergear los contactos no hubo deals
                                        utms_from_person(deal_to_assign)
                                    print("end merge deals")
                                    # MERGE DEAL
                                
                                    
                                else:
                                    print("Merge Error!")
                                    merge_results.append("Ha habido un error al mergear las personas")
                            except Exception as e:
                                print(e)
                                merge_results.append('Merge Person Error:' + str(e))
                                print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE D")                                       
                    else:
                        # no hay contactos por fusionar
                        if automatic_assign["peding_deals"] == True:
                            print("respose has pending deals")
                            for current_deal in automatic_assign["open_deals"]:
                                print("fusionar " + str(current_deal) + " con " + str(deal['deal_id']) + " este ultimo manda.")

                                try:
                                    merge_deal_url = (
                                        os.environ['PIPE_URL']
                                        + "deals/" +  str(current_deal)
                                        + "/merge?api_token="
                                        + os.environ['PIPE_TOKEN']
                                    )
                                    mergeDealBody = json.dumps({
                                        "merge_with_id": automatic_assign["oldest_deal"]
                                    })
                                    headers = {
                                      'Content-Type': 'application/json',
                                      'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
                                    }
                                    #+ "deals/" + str(current_deal)
                                    #"merge_with_id": deal['deal_id'] # el deal que ya existía
                                    #r = requests.put(merge_deal_url, headers={}, json=mergeDealBody)
                                    r = requests.request("PUT", merge_deal_url, headers=headers, data=mergeDealBody)
                                    print("result: ")
                                    print (json.loads(r.text))
                                    merge_deal_result = json.loads(r.text)                            
                                    if merge_deal_result['success'] == True:
                                        merge_deal_results.append("fusionado " + str(current_deal) + " con " + str(deal['deal_id']) + " este ultimo manda.")
                                        # Despues de mergear los deals no hubo contactos
                                        utms_from_person(deal_to_assign)
                                    else:
                                        print("Merge Error!")
                                        merge_deal_results.append("Ha habido un error al mergear los deals")
                                except Exception as e:
                                    print("merge deal exception")
                                    print(e)
                                    merge_deal_results.append('Merge Deal Error:' + str(e))
                                    print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE E") 
                        else:
                            #Sin deals por fusionar
                            print("No deals por fusionar")
                            # Sin contactos ni deals por fusionar
                            utms_from_person(deal_to_assign)
                        print("end merge deals")
                        # MERGE DEAL

                else:
                    results.append('Ha habido un problema al asignar el deal ' + str(deal['deal_id']) + ' a ' + str(automatic_assign_id))

            except Exception as e:
                print(e)
                results.append('Assign Error:' + str(e))
                print("NO TOKEN INFO FOUND, SKIPPING X")               
        
        response['results'] = results
        response['merge_result'] = merge_results
        response['merge_deal_result'] = merge_deal_results
        print("=========RESPONSE=================")
        print(response)
        print("======== NOTIFICATION ============")
        #if automatic_assign["assignment_type"] == "bad contact information Gloria/Hiram" or "":
        #    send_with_ses("Revisión requerida", "Información de contacto insuficiente", "jperez@contalink.com", "jperez@contalink.com")
        
        return response

    except Exception as ex:
        traceback.print_exc()
        if timbrada == False:
            response['status'] = 0
            response['message'] = str(ex)
            print(json.dumps(response))
        return response
        
def add1stActivityToVADeal(deal_id):
    print("add first act")
    os.environ['PIPE_URL'] = "https://contalink.pipedrive.com/api/v1/"
    #os.environ['PIPE_TOKEN'] = "134bde7bf737a397258c8b463194e808e4fe1ad5" # Gloria
    os.environ['PIPE_TOKEN'] = "0265cdd4911c8d00da7b508d60ec5171fa4b5e00" # Tecnología
    response = {}
    try:
        headers = {
          'Content-Type': 'application/json',
          'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
        }        
        url = (
            os.environ['PIPE_URL']
            + "activities?api_token="
            + os.environ['PIPE_TOKEN']
        )
        
        activityBody = json.dumps({
            "deal_id": str(deal_id),
            "user_id": 5995501,
            "done": 0,
            "subject":"1er contacto - VA"
        })
        r = requests.request("POST", url, headers=headers, data=activityBody)
        result = json.loads(r.text)
        if result['success'] == True:
            print("add first act Success")
            response['deal_id'] = deal_id
            response['status'] = 'success'
            return response
        else:
            print("add first act Error")
            response['status'] = 'error'
            response['message'] = 'algo ha salido mal al crear la actividad de Pipedrive'
            return response         
            
    except Exception as e:
        response['status'] = 'error'
        response['message'] = e
        return response            

def vaActions(action, deal_id, params):
    print("Acciones adicionales.")
    os.environ['PIPE_URL'] = "https://contalink.pipedrive.com/api/v1/"
    #os.environ['PIPE_TOKEN'] = "134bde7bf737a397258c8b463194e808e4fe1ad5" # Gloria
    os.environ['PIPE_TOKEN'] = "0265cdd4911c8d00da7b508d60ec5171fa4b5e00" # Tecnología
    
    #Actions
    if action == "OPEN_AND_PTE_1ER_PAGO":
        try:
            full_url = (
                os.environ['PIPE_URL']
                + "deals/" + str(deal_id)
                + "?api_token="
                + os.environ['PIPE_TOKEN']
            )
            #Gloria: 5995501 | Hiram: 11607065
            # TODO cuando cambie a CRON
            # el 11607065 pasa a automatic_assign_id
            updateBody = json.dumps({
                "status": 'open',
                "stage_id": 124
            })
            headers = {
              'Content-Type': 'application/json',
              'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
            }
            r = requests.request("PUT", full_url, headers=headers, data=updateBody)

            print("result: ")
            print (json.loads(r.text))
            result = json.loads(r.text)
            if result['success'] == True:
                print("Success")
                add1stActivityToVADeal(deal_id)
                return 'ok'
            else:
                return None
        except Exception as e:
            print(e)
            print("NO TOKEN INFO FOUND, SKIPPING PIPEDRIVE Z")                                           
            return 'error'

def addNoteAuxiliar(environment, agent_id, deal_id):
    #https://contalink.pipedrive.com/api/v1/activities/645316?api_token=0265cdd4911c8d00da7b508d60ec5171fa4b5e00
    # Configuración de Pipedrive (asegúrate de tener estas variables definidas)
    api_token =  os.environ['PIPE_TOKEN']
    base_url = "https://contalink.pipedrive.com/api/v1"
    base_url_2 = "https://contalink.pipedrive.com/api/v2"

    print(f"Buscando actividades '1er contacto' para el Deal {deal_id}...")
    print("Agente")
    print(agent_id)
    try:
        # 1. Obtener todas las actividades relacionadas con el deal_id
        # Usamos el endpoint /activities y filtramos por deal_id
        params = {
            'api_token': api_token,
            'deal_id': deal_id
        }
        
        response = requests.get(f"{base_url_2}/activities?api_token={api_token}&deal_id={deal_id}")
        response.raise_for_status()
        activities_data = response.json()
        print("ACt II")
        print(activities_data)
        if not activities_data.get('data'):
            print(f"No se encontraron actividades para el deal {deal_id}")
            #unset_auxiliar_in_deal(environment, deal_id)
            return False

        updated_count = 0

        # 2. Iterar y filtrar por el título exacto "1er contacto"
        print("Buscar 1er contacto")
        for activity in activities_data['data']:
            if activity.get('subject', '').startswith("1er contacto"):
                activity_id = activity['id']
                
                # 3. Actualizar el dueño (user_id) de la actividad
                update_url = f"{base_url}/activities/{activity_id}?api_token={api_token}"
                update_payload = {
                    'user_id': agent_id
                }
                print("UPDATE URL")
                print(update_url)
                update_res = requests.put(update_url, json=update_payload)
                
                if update_res.status_code == 200:
                    print(f"Actividad {activity_id} reasignada con éxito al agente {agent_id}")
                    updated_count += 1
                else:
                    print(f"Error al actualizar actividad {activity_id}: {update_res.text}")
                    #unset_auxiliar_in_deal(environment, deal_id)

        print(f"Proceso terminado. Actividades actualizadas: {updated_count}")
        return True

    except Exception as e:
        print(f"Error en addNoteAuxiliar: {e}")
        #unset_auxiliar_in_deal(params, deal_id)
        return False


def get_type_lead_priority(persist_deal, open_deals):
    print("Get Type Lead Priority")
    """
    Evalúa la prioridad del tipo de lead entre varios deals usando un solo GET.
    Retorna si es necesario actualizar y cuál es el valor ganador.
    """
    # 1. Preparar la lista de todos los IDs a consultar
    # Aseguramos que persist_deal sea el primer elemento y concatenamos
    all_ids = [str(persist_deal)] + [str(d) for d in open_deals]
    ids_string = ",".join(all_ids)
    
    url = (
        os.environ['PIPE_URL_V2']
        + "deals?ids=" + ids_string
        + "&api_token=" + os.environ['PIPE_TOKEN']
    )
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
    }
    
    # 2. Realizar la petición GET
    try:
        r = requests.request("GET", url, headers=headers)
        result = json.loads(r.text)
        print("INFO DE DEALS V2")
        print(result)
    except Exception as e:
        print("Error al consultar deals para prioridad:", e)
        return {"update": False, "type_lead": None}
        
    if not result.get('success') or not result.get('data'):
        return {"update": False, "type_lead": None}

    # 3. Definir la jerarquía de prioridades
    hierarchy = {
        '347': 4, # Recontratación
        '698': 3, # Referido
        '345': 2, # Nuevo Prospecto
        '711': 1  # Sin Intención
    }
    
    custom_field = '3098fab920387ade3b098c60b1230bdb516723d8'
    
    highest_weight = -1
    highest_val = None
    persist_deal_val = None

    # 4. Iterar sobre la respuesta de Pipedrive para encontrar el ganador
    for deal in result['data']:
        deal_id = str(deal['id'])
        val = deal.get("custom_fields").get(custom_field)
        print("deal:")
        print(deal_id)
        print("tipo")
        print(val)
        # Obtener el peso numérico (si es nulo o no existe en la jerarquía, es 0)
        weight = hierarchy.get(str(val), 0) if val else 0
        
        # Guardar el valor más alto encontrado en todos los deals
        if weight > highest_weight:
            highest_weight = weight
            highest_val = val
            
        # Guardar específicamente el valor del deal que va a persistir
        if deal_id == str(persist_deal):
            persist_deal_val = val
            
    # 5. Evaluar si el deal persistente necesita actualización
    persist_weight = hierarchy.get(str(persist_deal_val), 0) if persist_deal_val else 0
    needs_update = highest_weight > persist_weight
    
    return {
        "update": needs_update,
        "type_lead": highest_val
    }


def update_type_lead_priority(type_lead, deal_id):
    print("Update type_lead priority")
    """
    Actualiza el campo personalizado de prioridad en el deal sobreviviente.
    """
    print("deal")
    print(deal_id)
    print("type:")
    print(type_lead)
    if type_lead is None:
        print("No hay un type_lead válido para actualizar.")
        return
        
    url = (
        os.environ['PIPE_URL']
        + "deals/" + str(deal_id)
        + "?api_token=" + os.environ['PIPE_TOKEN']
    )
    
    # 1. Preparar el cuerpo de la petición (PUT)
    updateBody = json.dumps({
        "3098fab920387ade3b098c60b1230bdb516723d8": type_lead
    })
    
    headers = {
        'Content-Type': 'application/json',
        'Cookie': '__cf_bm=jewMH6ktzw7.I6MYT9KeBWWBEp1.DQS.KIUw0SVgkY8-1638816836-0-AWbeFVH6rqVDeHHsKu90ik3FkyrdJnnpAvGDv+hXUP/baRE5kUsWrqtkcoOSQLuT6TXQdaseK4G0oYjEAUjU2nk='
    }
    
    # 2. Ejecutar la actualización
    try:
        r = requests.request("PUT", url, headers=headers, data=updateBody)
        result = json.loads(r.text)
        
        if result.get('success'):
            print(f"Éxito: Prioridad del deal {deal_id} actualizada a {type_lead}")
        else:
            print(f"Error en Pipedrive al actualizar prioridad del deal {deal_id}:", result)
    except Exception as e:
        print(f"Excepción HTTP al actualizar prioridad del deal {deal_id}:", e)