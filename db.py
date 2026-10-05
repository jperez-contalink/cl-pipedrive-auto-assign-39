import json
import psycopg2
import os

def get_connection(env):
    params = get_db_parameters(env)
    conn = psycopg2.connect(**params)
    return conn

def get_db_parameters(env):
    return_params = {}
    
    return_params['host'] =  os.environ[env.upper() + '_' + 'DB_HOST']
    return_params['database'] = os.environ[env.upper() + '_''DB_NAME']
    return_params['user'] = os.environ[env.upper() + '_''DB_USER']
    return_params['password'] = os.environ[env.upper() + '_''DB_PASS']    
    return return_params
