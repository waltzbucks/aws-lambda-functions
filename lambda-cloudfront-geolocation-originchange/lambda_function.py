#!/usr/bin/env python

import logging

logging.getLogger().setLevel(logging.INFO)

def lambda_handler(event, context):
    
    logging.info('event::{}'.format(event))

    try:
        request_dict = event.get('Records')[0].get('cf').get('request')
        request_headers = request_dict.get('headers')
        req_host = request_headers.get('host')[0]['value']
        
        if request_headers['cloudfront-viewer-country'][0]['value'] != 'KR':
            
            logging.info('Cloudfront-Viewer-Country: ' + str(request_headers['cloudfront-viewer-country'][0]['value']))
            logging.info(request_dict.get('uri'))
            
            custom_origin = {
                "custom": {
                    "customHeaders": {},
                    "domainName": "", #TODO Input this field for changed origin domain 
                    "keepaliveTimeout": 5,
                    "path": "",
                    "port": 80,
                    "protocol": "http",
                    "readTimeout": 30,
                    "sslProtocols": [
                        "TLSv1",
                        "TLSv1.1",
                        "TLSv1.2"
                    ]
                }
            }
            
            logging.info('custom_origin::{}'.format(custom_origin))
            
            request_dict['origin'] = custom_origin
            request_dict['headers']['host'] = [{
                'key': 'Host',
                'value': 'www.example.com'
            }]
            
            logging.info('custom_origin::{}'.format(request_dict))
            
        return request_dict
            

    except Exception as e:
        logging.error('exception::{1}'.format(e.args[0], e))

        return {
            'status': 500,
            'statusDescription': 'Internal server error',
        }

    logging.info('request_dict::{}'.format(request_dict))