import logging

def printResponse(response):
    print("{}: {}".format(response.status_code, response.text))

def enableHttpDebugLevel():
    # These two lines enable debugging at httplib level (requests->urllib3->http.client)
    # You will see the REQUEST, includinpg HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
    # The only thing missing will be the response.body which is not logged.
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1

    # Set the logging levels for requests
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    
def formatedLogs(msg):
    print("---------------------------------------")
    print(msg)
    print("---------------------------------------")