import json
import requests
from db import get_connection
from psycopg2.extras import RealDictCursor
import os
from util import crm_assign_user_to_deal

def get_automatic_assign(db_params, deal_id):
    conn = get_connection(db_params)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)
    sql_cmd = "SELECT crm_assign_user_to_deal as json_data from (SELECT * FROM system_utils.crm_assign_user_to_deal(%s)) x;"
    #sql_cmd = "SELECT (system_utils.crm_assign_user_to_deal(%s)->>'user')::json->>'id' as json_data"
    sql_params = (deal_id,)
    cur.execute(sql_cmd, sql_params)
    row = cur.fetchone()
    cur.close()
    print ("SQL", deal_id)
    return row['json_data']

def get_automatic_va_assign(db_params, deal_id):
    conn = get_connection(db_params)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)
    #sql_cmd = "SELECT crm_assign_user_to_va_deal as json_data from (SELECT * FROM system_utils.crm_assign_user_to_va_deal(%s)) x;"
    # Nueva función que sólo tiene 3 acciones posibles.
    sql_cmd = "SELECT crm_assign_user_to_va_deal_v2 as json_data from (SELECT * FROM system_utils.crm_assign_user_to_va_deal_v2(%s)) x;"
    sql_params = (deal_id,)
    cur.execute(sql_cmd, sql_params)
    row = cur.fetchone()
    cur.close()
    print ("SQL", deal_id)
    return row['json_data']

def get_all_pending_deals(db_params):
    conn = get_connection(db_params)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)
    #sql_cmd = "SELECT id as deal_id from (SELECT * FROM system_utils.crm_deal WHERE is_temporal_assigned = false  AND stage_id = 249  AND status ILIKE '%open%' LIMIT 1) x;"
    sql_cmd = "SELECT id as deal_id from (SELECT * FROM system_utils.crm_deal WHERE is_temporal_assigned = false  AND stage_id = 249  AND status ILIKE '%open%' AND COALESCE(system_status, '') <> 'LOCK' LIMIT 1) x;"
    cur.execute(sql_cmd)
    rows = list(cur.fetchall())
    cur.close()
    if rows is None:
        return None
    else: 
        return rows

def get_all_va_deals(db_params):
    conn = get_connection(db_params)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # toma los deals ingresados hasta media hora después de que se crearon, para dar tiempo de pagar inmediata
    #sql_cmd = "SELECT id as deal_id from (SELECT * FROM system_utils.crm_deal WHERE COALESCE(va_auto_merge, false) = false  AND stage_id IN (213, 124)  AND (status ILIKE '%open%' OR status ILIKE '%won%') AND canal_venta::integer IN (425, 426) AND add_time > '2024-12-12 00:00:00' AND (EXTRACT(EPOCH FROM (NOW() - add_time::timestamp)) / 3600) > 1 LIMIT 1) x;"
    sql_cmd = "SELECT id as deal_id from (SELECT * FROM system_utils.crm_deal WHERE COALESCE(va_auto_merge, false) = false  AND stage_id IN (213, 124)  AND (status ILIKE '%open%' OR status ILIKE '%won%') AND canal_venta::integer IN (425, 426) AND add_time > '2024-12-12 00:00:00' AND (EXTRACT(EPOCH FROM (NOW() - add_time::timestamp)) / 60) > 10 LIMIT 1) x;"
    
    # Querys Pruebas
    #sql_cmd = "SELECT id as deal_id from (SELECT * FROM system_utils.crm_deal WHERE COALESCE(va_auto_merge, false) = false  AND stage_id IN (213, 124)  AND (status ILIKE '%open%' OR status ILIKE '%won%') AND canal_venta::integer IN (425, 426) AND id = 144299 LIMIT 1) x;"
    #sql_cmd = "SELECT id as deal_id from (SELECT * FROM system_utils.crm_deal WHERE  id = 96829 LIMIT 1) x;"
    cur.execute(sql_cmd)
    rows = list(cur.fetchall())
    cur.close()
    if rows is None:
        return None
    else: 
        return rows

def unset_auxiliar_in_deal(db_params, deal_id):
    conn = get_connection(db_params)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)
    sql_cmd = "UPDATE system_utils.crm_deal SET auxiliar_agent = null WHERE id = %s;"
    sql_params = (deal_id,)
    cur.execute(sql_cmd, sql_params)
    #row = cur.fetchone()
    cur.close()
    print ("SQL", deal_id)
    return "ok"

def set_assign_deal_to_true(db_params, deal_id):
    conn = get_connection(db_params)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)
    sql_cmd = "UPDATE system_utils.crm_deal SET is_temporal_assigned = true WHERE id = %s;"
    sql_params = (deal_id,)
    cur.execute(sql_cmd, sql_params)
    #row = cur.fetchone()
    cur.close()
    print ("SQL", deal_id)
    return "ok"

def set_va_deal_to_true(db_params, deal_id):
    conn = get_connection(db_params)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)
    sql_cmd = "UPDATE system_utils.crm_deal SET va_auto_merge = true WHERE id = %s;"
    sql_params = (deal_id,)
    cur.execute(sql_cmd, sql_params)
    #row = cur.fetchone()
    cur.close()
    print ("SQL", deal_id)
    return "ok"    

def set_va_deal_record_deal_id(db_params, deal_id, new_deal_id):
    conn = get_connection(db_params)
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)
    sql_cmd = "UPDATE system_utils.landing_record SET pipedrive_id = %s WHERE pipedrive_id = %s;"
    sql_params = (new_deal_id, deal_id)
    cur.execute(sql_cmd, sql_params)
    #row = cur.fetchone()
    cur.close()
    print ("SQL", deal_id)
    return "ok" 

def get_phone_number(data):
    try:
        phone_numbers = data.get("data", {}).get("person_id", {}).get("phone", [])
        primary_phone = next((phone["value"] for phone in phone_numbers if phone.get("primary")), None)
        if primary_phone:
            phone_number = primary_phone.replace(" ", "")
            return phone_number
        return None
    except Exception as e:
        print(f"Error al obtener numero de telefono: {e}")
        return None
        

def validate_data(data):
    try:
        phone_number = get_phone_number(data)
        status = data.get("data", {}).get("status", {})
        next_activity_subject = data.get("data", {}).get("next_activity_subject", {})
        contact_medium = data.get("data", {}).get("eaf8d47de8714896fff87d841884cc6a7d3367f9", {})
        print('Telefono: ')
        print(phone_number)
    
        print('Estatus deal: ')
        print(status)
    
        print('contact_medium: ')
        print(contact_medium)

        print('Next Activity')
        print(next_activity_subject)

        if phone_number == "" or phone_number is None: return False # Si no viene vacio entonces continua con el flujo
        if status != "open" or status is None: return False # Si el deal no esta abierto retorno false
        if "1er contacto 2.2 Teléfono - WhatsApp Bot" in next_activity_subject: return False # Omitir todas las de whatsapp
        if next_activity_subject is None or "1er contacto" not in next_activity_subject: return False # Si el deal no es primer contacto retorno false
        #contact_mediums = ["1.2 Pagina Web - Info form", "4.2 Facebook - Messenger", "5.1 Mail"]
        contact_mediums = ["430", "435", "436"]
        avoid_contact_mediums =  ["431", "432"]
        print('Validacion exitosa del deal')
        # Retornar True para todos menos para los medios de contacto Whatsapp
        #return True if any(string in contact_medium for string in contact_mediums) else False
        return False if contact_medium in avoid_contact_mediums else True

    except Exception as e:
        print(f"Error al validar la informacion del deal: {e}")
        return False
        

def send_hilos_flow_api(phone_number):
    try:
        print('Se envia el numero de telefono al flujo de hilos')
        #flow_id = "78e769d9-1ea4-4564-89cb-0333b3ef3092" # --> Flujo solicitar info wap (nuevo)
        flow_id = "06836055-c564-7db4-8000-bc5e54d7c209" # --> último flujo con horario de llamada v.2.3.1
        hilos_url = (
            "https://api.hilos.io/api/flow/"
            + flow_id + "/run"
        )
    
        print(hilos_url)
        payload = {
            "execute_for": "LIST",
            "contact_list": [
                {
                    "phone": phone_number
                }
            ]
        }
    
        headers = {
            "Authorization": os.environ.get('HILOS_TOKEN_AUTH'),
            "Content-Type": "application/json"
        }
    
        response = requests.post(hilos_url, json=payload, headers=headers)
        
        if response.status_code == 200 or  response.status_code == 201:
            data = response
            print('Respuesta del flujo: ')
            print(data)
        else:
            print(f"Error: Error en llamada api hilos {response.status_code}")
    except Exception as e:
        print(f"Error enviando flujo al API de hilos")
    
from psycopg2.extras import RealDictCursor

def set_auxiliar_agent(db_params, deal_id):
    """
    Ejecuta la lógica de balanceo diario en PostgreSQL y asigna 
    un agente auxiliar al deal especificado.
    """
    try:
        conn = get_connection(db_params)
        # Es importante que autocommit sea True para que el UPDATE se guarde inmediatamente
        conn.autocommit = True 
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Llamamos a la función que creamos: system_utils.assign_next_auxiliar_agent
        sql_cmd = "SELECT response FROM system_utils.assign_next_auxiliar_agent(%s);"
        sql_params = (deal_id,)
        
        cur.execute(sql_cmd, sql_params)
        row = cur.fetchone()
        
        cur.close()
        conn.close()

        if row and 'response' in row:
            # Retorna el diccionario {'next_auxiliar_agent': 12345}
            return row['response']
        
        return {"error": "No se pudo obtener respuesta de la función"}

    except Exception as e:
        print(f"Error al asignar agente auxiliar para el deal {deal_id}: {e}")
        return {"error": str(e)}

# Ejemplo de uso:
# result = set_auxiliar_agent(db_params, 10500)
# print(result['next_auxiliar_agent'])

def send_template_hilo(deal_id):
    try:
        api_token = "0265cdd4911c8d00da7b508d60ec5171fa4b5e00"
        pipe_drive_url = (
            "https://contalink.pipedrive.com/api/v1/deals/"
            + str(deal_id) + "?api_token=" + api_token
        )

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.get(pipe_drive_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print('Informacion del deal: ')
            print(data)
            if validate_data(data):
                send_hilos_flow_api(get_phone_number(data))
        else:
            print(f"Error codigo {e}")
    except Exception as e:
        print(f"Error al obtener informacion del deal: {e}")
            

def get_automatic_assign_python(db_params, deal_id, *, commit=True, debug=False):
    """
    Reemplazo Python de get_automatic_assign().

    commit=True  -> comportamiento normal del Lambda.
    commit=False -> útil para pruebas controladas: ejecuta toda la lógica y
                    hace ROLLBACK al final.
    """
    conn = get_connection(db_params)
    conn.autocommit = False

    try:
        result = crm_assign_user_to_deal(
            conn,
            deal_id,
            mark_temporal_assigned=False,
            debug=debug,
        )

        if commit:
            conn.commit()
        else:
            conn.rollback()

        return result

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()