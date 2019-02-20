import cherrypy as cp
from lib import handle_error, validate


# Ping microservice
class Ping(object):
    exposed = True

    def __init__(self, cas_server, serviceID):
        self.cas_server = cas_server
        self.serviceID = serviceID

    def GET(self):

        if validate(cp.request.headers, self.cas_server, self.serviceID):
            try:
                return handle_error(200, "Pong")
            except:
                return handle_error(500, "Internal Server Error")
        else:
            return handle_error(401, "Unauthorized")


