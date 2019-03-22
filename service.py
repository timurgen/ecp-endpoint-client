"""
Simple ECP endpoint client for Sesam.io powered applications
"""
import os
import logging
import json
import time
import zeep

from flask import Flask, request, Response
from utils import strings, date
from infrastructure.ecp_endpoint import ECPClient

# debug mode or not
DEBUG = strings.str_to_bool(os.environ.get('DEBUG', "false"))

# listening on port
PORT = int(os.environ.get('PORT', '5000'))

# content type response header
CT = os.environ.get('CONTENT_TYPE', 'application/json')

# wsdl file location public ECP service default
WSDL = os.environ.get('WSDL', 'http://ecp.entsoe.eu/ECP_MODULE/services/ECPEndpointService?wsdl')

# ECP endpoint URL, not required if WSDL property points to ECP node
ECP_ENDPOINT = os.environ.get('ECP_ENDPOINT')

# will wait for "RECEIVED" or "FAILED" status for each entity before writing back to Sesam
CONFIRM_RECEIVE = strings.str_to_bool(os.environ.get('CONFIRM_RECEIVE', 'false'))

# confirm receive timeout
RECEIVE_TIMEOUT = int(os.environ.get('RECEIVE_TIMEOUT', 5))

APP = Flask(__name__)

if not WSDL:
    logging.error("WSDL must be provided")
    exit(1)


@APP.route("/send", methods=['POST'])
def send():
    """
    send message endpoint, takes array of json objects with shape
    [{
        "_id": "<sesam id>",
        "receiverCode": "<destination endpoint>",
        "businessType": "<message type>",
        "content": "<string  content>",
        "senderApplication": "<sender application name>",
        "baMessageID": "<baMessageID>"
    }]
    :return: input data populated with message id from ECP or full transfer details if
    CONFIRM_RECEIVE enabled
    """

    def generate_response():
        """
        make request to ECP endpoint and output result
        :return: streamed json array
        """
        yield '['

        first = True

        for item in payload:
            if not first:
                yield ','
            item['content'] = item['content'].encode('utf-8')

            response = service.SendMessage(item)
            item['ecp_message_id'] = response

            item['content'] = item['content'].decode('utf-8')

            if CONFIRM_RECEIVE and 1 == 2:
                start_time = time.time()

                while time.time() - start_time < RECEIVE_TIMEOUT:
                    time.sleep(1)  # checkMessageStatus may return error if checking immediately
                    msg_status = service.CheckMessageStatus(messageID=item['ecp_message_id'])

                    logging.debug(msg_status)

                    item['ecp_message_status'] = msg_status['state']
                    item['ecp_message_details'] = zeep.helpers.serialize_object(msg_status)

                    if msg_status['state'] in ['RECEIVED', 'FAILED']:
                        break

            yield json.dumps(item, default=date.json_serial)
        yield ']'

    payload = request.get_json()
    service = ECPClient.get(WSDL, override_url=None if not ECP_ENDPOINT else ECP_ENDPOINT)
    return Response(generate_response(), content_type=CT)


@APP.route("/check", methods=['POST'])
def check():
    """
    check message status endpoint, takes array of json objects with shape
    [{
        "_id": "<sesam id>",
        "ecp_message_id": "<previously assigned ECP id>",
    }]
    :return: input data populated with  transfer details
    """

    def generate_response():
        """
        make request to ECP endpoint and output result
        :return: streamed json array
        """
        yield '['

        first = True

        for item in payload:
            if not first:
                yield ','

            msg_status = service.CheckMessageStatus(messageID=item['ecp_message_id'])
            logging.debug(msg_status)

            item['ecp_message_status'] = msg_status['state']
            item['ecp_message_details'] = zeep.helpers.serialize_object(msg_status)

            yield json.dumps(item, default=date.json_serial)
        yield ']'

    payload = request.get_json()
    service = ECPClient.get(WSDL, override_url=None if not ECP_ENDPOINT else ECP_ENDPOINT)

    return Response(generate_response(), content_type=CT)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    if not DEBUG:
        import cherrypy

        cherrypy.tree.graft(APP, '/')
        cherrypy.config.update({
            'environment': 'production',
            'engine.autoreload_on': True,
            'log.screen': True,
            'server.socket_port': PORT,
            'server.socket_host': '0.0.0.0',
            'server.thread_pool': 10,
            'server.max_request_body_size': 0
        })

        cherrypy.engine.start()
        cherrypy.engine.block()
    else:
        APP.run(threaded=True, debug=DEBUG, host='0.0.0.0', port=PORT)
