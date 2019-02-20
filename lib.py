import cherrypy
from cherrypy import log
import json
import requests
from xml.etree import ElementTree


# get list of parameters from Web Service invocation
def get_parameters(params, pname):

    parameters = params[pname]
    if type(parameters) == str:
        parameters = [parameters]
    return parameters


def handle_error(code, message, ctx="HTTP"):

    if code == 500:
        traceback = True
    else:
        traceback = False

    log.error(msg=message, context=ctx, traceback=traceback)
    cherrypy.response.status = code
    ctype = "application/json;charset=utf-8"
    cherrypy.response.headers["Content-Type"] = ctype

    return json.dumps({"code": code, "message": message}).encode('utf8')


def singlequote(value):

    return "'" + value + "'"


def validate(headers, cas_server, serviceID):

    # FIXME
    return True

    token = headers["X-Auth-Token"]

    url = (cas_server + "/p3/serviceValidate?service=" + serviceID + "&ticket=" + token)
    r = requests.get(url, verify="/etc/ssl/certs/ca.pem")
    root = list(ElementTree.fromstring(r.content))

    return root[0].tag.endswith("authenticationSuccess")
