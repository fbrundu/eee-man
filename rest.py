import cherrypy as cp
import json
from multiprocessing import Pool
from services import Ping, ManchesterEEE


def start():

    # load configuration
    with open("conf/conf.json", "r") as cfile:
        pbc = json.load(cfile)

    # start Web Service with some configuration
    if pbc["stage"] == "production":
        global_conf = {
               "global":    {
                                "server.environment": "production",
                                "engine.autoreload.on": False,
                                "engine.autoreload.frequency": 5,
                                "server.socket_host": "0.0.0.0",
                                "log.screen": False,
                                "log.access_file": "eee.log",
                                "log.error_file": "eee.log",
                                "server.socket_port": pbc["port"]
                                # "server.ssl_module": "builtin",
                                # "server.ssl_certificate": pbc["cert"],
                                # "server.ssl_private_key": pbc["priv"],
                                # "server.ssl_certificate_chain": pbc["chain"]
                            }
    }
        cp.config.update(global_conf)
    conf = {
        "/": {
            "request.dispatch": cp.dispatch.MethodDispatcher(),
            "tools.encode.debug": True,
            "request.show_tracebacks": False
        }
    }

    pool = Pool(3)

    # FIXME
    serviceID = "DH_simulator"
    service_path = "eee"

    cp.tree.mount(Ping(pbc["aurl"], serviceID),
                  "/" + service_path + "/ping", conf)
    cp.tree.mount(ManchesterEEE(pbc["mlab_path"],
                                pool,
                                pbc["broker"],
                                pbc["aurl"],
                                serviceID,
                                "HTTP",
                                pbc["acert"],
                                pbc["b_mapping"],
                                pbc["username"],
                                pbc["password"]),
                  "/" + service_path + "/manchester_eee", conf)


    # activate signal handler
    if hasattr(cp.engine, "signal_handler"):
        cp.engine.signal_handler.subscribe()

    # start serving pages
    cp.engine.start()
    cp.engine.block()
