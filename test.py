import json
import os
from lambda_function import lambda_handler

def get_event_json():
    with open('request.json') as json_data:
        d = json.load(json_data)
    return d

def set_env_vars():
    os.environ['BUCKET_UPLOAD'] = "erp-tegik"
    os.environ['VALIDATE_SCHEME'] = "False"
    os.environ['TIMBRAR'] = "True"
    os.environ['TIEMPO_ESPERA'] = "60000"
    os.environ['CFDI_VERSION'] = "3.3"
    os.environ['PROVEEDOR_TIMBRADO'] = "Detecno"
    os.environ['TIPO_COMPROBANTE'] = "I"
    os.environ['METODO_PAGO'] = "PPD"
    os.environ['FORMA_PAGO'] = "99"

print ("JPS TEST")
# Setea variables de entorno
set_env_vars()
# Obtiene el json request, aca este el id del documento
event = get_event_json()
# A partir de aa obtiene el documento de la base de datos, contruye el xml y request.
response = lambda_handler(event, None)
#print(json.dumps(response))
