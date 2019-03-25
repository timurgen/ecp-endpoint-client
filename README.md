# ecp-endpoint-client
Simple ECP endpoint client for Sesam.io powered applications

Env vars: 

* DEBUG - debug mode or not - default false
* PORT - listening on port - default 5000
* WSDL - wsdl file location
* ECP_ENDPOINT - ECP endpoint URL, not required if WSDL property points to ECP node 
* CONFIRM_RECEIVE - will wait for "RECEIVED" or "FAILED" status for each entity before writing back to Sesam  if true - default false
* RECEIVE_TIMEOUT - confirm receive timeout in seconds - default 5 sec

## Entity shape for `send` endpoint 

```json
    [{
        "_id": "<sesam id>",
        "receiverCode": "<destination endpoint>",
        "businessType": "<message type>",
        "content": "<string  content>",
        "senderApplication": "<sender application name>",
        "baMessageID": "<baMessageID>"
    }]
```


## Entity shape for `check` endpoint 
```json
    [{
        "_id": "<sesam id>",
        "ecp_message_id": "<previously assigned ECP id>",
    }]
```
