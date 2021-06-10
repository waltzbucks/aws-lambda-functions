import json
import logging
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch import helpers
from aws_requests_auth.aws_auth import AWSRequestsAuth


logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

logging.basicConfig(format = '%(created)f:%(levelname)s:%(funcName)s:%(message)s', level=logging.INFO)


def load_config(context):
    
    logging.info(context)
    
    # Check version
    function_name = context.function_name
    alias = context.invoked_function_arn.split(':').pop()

    if function_name == alias:
        alias = '$LATEST'
        print("No Version Set - Default to $LATEST")


    # Set config
    with open('es-access-config.json') as json_data:
        config = json.load(json_data)

    print("Succesfully loaded config")
    return config

def sts_auth(config):
    logging.info(config)
    
    # Genarate auth request to connect AWS ES
    sts = boto3.client('sts')

    creds = sts.assume_role(
        RoleArn=config['sts_role_arn'], RoleSessionName=config['sts_session_name'])

    auth = AWSRequestsAuth(aws_access_key=creds['Credentials']['AccessKeyId'],
                           aws_secret_access_key=creds['Credentials']['SecretAccessKey'],
                           aws_host=config['es_host'],
                           aws_region=config['es_region'],
                           aws_service='es',
                           aws_token=creds['Credentials']['SessionToken'])
    return auth

def write_bulk(record_set, es_client, config):
    logging.info("Writing data to ES")
    
    # Write the data set to ES, chunk size has been increased to improve performance
    
    resp = helpers.bulk(es_client,
                        record_set,
                        chunk_size=config['es_bulk_chunk_size'],
                        timeout=config['es_bulk_timeout'])
    return resp

def datascan(es_client,event):
    logging.info("search the data to ES")
    logging.info("ES Client=" + str(es_client))
    logging.info("Event=" + str(event))
    
    searchquery = queries(event)
    resp = helpers.scan(client=es_client,
                        query=searchquery,
                        index="cloudaffairempldb*")
    
    results_list = []

    for hit in resp:
        
        results_list.append(hit["_source"])
    
    return results_list

def queries(event):
    
    # Search query processing
    param_queries = event["queryStringParameters"]
    
    if "q" in param_queries:
        query = {
            "size": 5,
            "query": {
                "query_string": {
                "query": param_queries["q"]
                }
            }
        }
    
    else:
        query = {"query": {"match": param_queries }}
    
    logging.info("search query=" + str(query))
    
    return query
    
    
def lambda_handler(event, context):
    logging.info(event)
    logging.info(context)
    
    # Invoke Lambda
    # load config 
    config = load_config(context)
        
    # create ES connection with sts auth file
    es_client = Elasticsearch(host=config['es_host'],
                              scheme="https",
                              port=443,
                              http_auth=sts_auth(config),
                              timeout=config['es_connection_timeout'],
                              connection_class=RequestsHttpConnection)
    try:
        resp = json.dumps(datascan(es_client,event))
        logging.info("Return=" + str(resp))
        
        return {
            "statusCode": "200",
            "body": resp
        }
        
    except:
        return {
            "statusCode": "500"
        }
    
    