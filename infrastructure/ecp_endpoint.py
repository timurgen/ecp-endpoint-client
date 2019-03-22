"""
Provide functions to access SOAP client for ECP endpoint
"""
from zeep import Client


class ECPClient:
    _service = None
    _binding = "{http://ecp.entso-e.eu/}ECPEndpointSOAP12"

    @classmethod
    def get(cls, wsdl_location, override_url=None):
        """
        Build and return new SOAP service for given ECP_ENDPOINT
        :param wsdl_location:
        :param override_url:
        :return:
        """
        if not cls._service:
            client = Client(wsdl_location)
            client.settings.strict = False

            if override_url:
                cls._service = client.create_service(cls._binding, override_url)
            else:
                cls._service = client.service
        return cls._service


def check_connectivity(service, endpoint):
    # TODO check if tracing message is actually received by endpoint with checkMessageStatus request
    trace_message_id = service.ConnectivityTest(endpoint)
    return True if trace_message_id else False

