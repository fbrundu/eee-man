import cherrypy as cp
from cherrypy import log
import datetime as dt
from lib import get_parameters, handle_error, singlequote, validate
import multiprocessing
import os
import paho.mqtt.client as mqtt
import pandas as pd
from pymatbridge import Matlab
import re
import requests
import uuid


class ManchesterEEE(object):
    exposed = True

    def __init__(self, mlab_path, pool, broker, cas_server, serviceID, ctx, cert, b_mapping,
                 username, password):
        self.mlab_path = mlab_path
        self.pool = pool
        self.broker = broker
        self.cas_server = cas_server
        self.serviceID = serviceID
        self.ctx = ctx
        self.cert = cert
        self.b_mapping = b_mapping
        self.username = username
        self.password = password

    @cp.tools.json_in()
    def POST(self, *paths, **params):

        # FIXME correct serviceID
        if validate(cp.request.headers, self.cas_server, self.serviceID):

            try:
                input_vars = cp.request.json
                reqid = str(uuid.uuid4())

                respath = os.path.join(os.path.abspath("results"), "manchester_eee")
                srcpath = os.path.abspath("mlab")
                os.makedirs(os.path.join(respath, reqid))

#
#                    day_type = schedule_day(simulation_day.weekday())
#                    day_temp = schedule_temp(self.wu_api, simulation_day,
#                                             self.ctx)
#                    iren_results = schedule_iren(simulation_day.weekday(),
#                                                 self.iren_ws, self.ctx)
#                    hosts, old_sched, exclusion = iren_results


                wargs = {
                    "mlab_path": self.mlab_path,
                    "input_vars": input_vars,
                    "reqid": reqid,
                    "respath": respath,
                    "srcpath": srcpath,
                    "username": self.username,
                    "password": self.password,
                    "cert": self.cert
                    }
                self.pool.apply_async(ManchesterEEE.worker, (), wargs) #,
#                                      callback=self.publish)

                return handle_error(202, "Reqid: " + reqid)
            except:
                return handle_error(500, "Internal Server Error")
        else:
            return handle_error(401, "Unauthorized")

    @classmethod
    def worker(cls, mlab_path, input_vars, reqid, respath, srcpath,
               username, password, cert):

        pname = multiprocessing.current_process().name
        ctx = "HTTP Worker " + pname
        res_dir = os.path.join(respath, reqid)

        get_all_data(username,
                     password,
                     input_vars["start"],
                     input_vars["end"],
                     cert,
                     res_dir)

	return "OK"

        mlab = Matlab(executable=mlab_path)
        mlab.start()

        try:
            # setting variables
            log.error(msg="Setting Matlab variables", context=ctx)
            success = True
            for v in input_vars.keys():
                success &= mlab_setvar(mlab, v, input_vars[v], ctx)

            if not success:
                log.error(msg="Unable to set some variables", context=ctx)
            else:
                # running simulation
                log.error(msg="Starting simulation", context=ctx)
                mlab.run_code("cd " + os.path.join("mlab", "manchester_eee"))
                # FIXME put entry script here
                #mlab.run_code("sched")
                log.error(msg="Simulation ended", context=ctx)
                with open(os.path.join(respath, reqid, "completed"), "w"):
                    pass
        finally:
            mlab.stop()

        # FIXME
        return "OK"

    def publish(self, result):

        client = mqtt.Client("eee-manchester", clean_session=False)
        client.connect(self.broker, 1883)
        client.publish("eee/manchester/results", result)
        client.disconnect()



def enrich_mapping(mapping, ST, fit_cert):

    filter_path = ""
    n_pages = get_npages_reg(ST, fit_cert, filter_path)

    for page in range(1, n_pages + 1):

#        print("REG: Retrieving page", page, "of", n_pages)

        parameters = ["page=" + str(page), "per_page=100"]

        registry_page = retrieve_reg(ST, fit_cert, filter_path=filter_path,
                                     parameters=parameters)

        try:
            for entry in registry_page["entries"]:

                if entry["meta"]["resource_type"] == "register":
                    e_name = entry["meta"]["meter"]["name"]
                    device = entry["meta"]["register"]
                elif entry["meta"]["resource_type"] == "virtual_meter":
                    e_name = entry["meta"]["virtual_meter"]["name"]
                    device = entry["meta"]["virtual_meter"]
                else:
                    print(entry, "not a register or a virtual_meter")

                if e_name in mapping.index:
                    mapping["Unit"] = device["unit"]
                    mapping["Type"] = get_type(e_name[-5])
                    mapping["URI"] = entry["data"]
        except:
            print(entry)
            raise


def get_all_data(username, password, start, end, fit_cert, res_dir):

    start, end = get_dates(start, end)

    ST = get_token(username, password, "<service_name>", fit_cert)

    mapping = get_mapping()

    enrich_mapping(mapping, ST, fit_cert)

    mapping.to_csv("conf/build_mapping_enriched.txt", sep='\t')

    for e_name in mapping.index:

        # print("DATA: Retrieving data for name:", e_name)

        e_type = mapping.ix[e_name, "Type"]
        # e_unit = mapping.ix[e_name, "Unit"]
        e_uri = mapping.ix[e_name, "URI"]
        e_build = mapping.ix[e_name, "BUILD_NAME"]
        filename = e_build + " " + e_type + ".csv"
        filepath = os.path.join(res_dir, filename)

        df_columns = ["Meter", "Name", "SerialNumber", "Register", "Date",
                      "StartTime", "Duration", "PeriodValue", "TotalValue",
                      "Unit"]
        data_df = pd.DataFrame(columns=df_columns)

        n_pages = get_npages_data(e_uri, ST, fit_cert, start, end)

        for page in range(1, n_pages + 1):
            try:

                data_df = update_data(data_df, page, ST, fit_cert, e_uri, start, end, e_name)

            except Exception:

                print(traceback.format_exc(), file=log)
                #import ipdb; ipdb.set_trace()

        data_df.to_csv(filepath, index=False)


def get_dates(start, end):

    start = dt.datetime.strptime(start, "%Y-%m-%d")
    end = dt.datetime.strptime(end, "%Y-%m-%d")
    start = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    return start, end


def get_mapping():

    mapping = pd.read_table("conf/build_mapping.txt", sep='\t', index_col=0)
    mapping["Unit"] = ""
    mapping["URI"] = ""
    mapping["Type"] = ""

    return mapping


def get_npages_data(data_ref, ST, cert, start, end):

    parameters = ["page=1", "per_page=100", "start=" + start, "end=" + end]

    data_page = retrieve_data(ST, cert, data_ref, parameters=parameters)

    total = data_page["total"]

    # ceiling hack (use math.ceil if you want)
    n_pages = -(-total // 100)

    return n_pages


def get_npages_reg(ST, cert, filter_path):

    # retrieve sensors from specific baricentro
    parameters = ["page=1", "per_page=100"]

    registry_page = retrieve_reg(ST, cert, filter_path=filter_path,
                                 parameters=parameters)

    total = registry_page["total"]

    # ceiling hack (use math.ceil if you want)
    n_pages = -(-total // 100)

    return n_pages


def get_token(l_username, l_password, l_serviceID, cert):

    r = requests.post("<cas_server>",
                      data={"username": l_username, "password": l_password},
                      verify=cert)

    l_TGT = re.search("TGT-", r.text).group()

    print("* TGT\t" + l_TGT)

    r = requests.post("<cas_server>" + l_TGT,
                      data={"service": l_serviceID}, verify=cert)

    l_ST = r.text

    print("* ST\t" + l_ST)

    return l_ST


def get_type(t):

    if t == "E":
        t = "Elec"
    elif t == "H":
        t = "Heat"
    elif t == "G":
        t = "Gas"
    elif t == "W":
        t = "Wate"
    else:
        print(t, "not recognized")

    return t


def mlab_setvar(mlab, key, value, ctx, asis=False):

    if not asis:
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                pass
            else:
                value = singlequote(value)
        else:
            value = str(value)

    statement = key + " = " + value + ";"
    log.error(msg=statement, context=ctx)
    result = mlab.run_code(statement)

    if not result["success"]:
        log.error(msg="Unable to set matlab variable " + key + ": " +
                  result["content"]["stdout"], context=ctx)
        return False

    return True


def retrieve_data(ST, cert, data_ref, parameters=[]):

    if parameters:
        parameters = '?' + '&'.join(parameters)
    else:
        parameters = ""

    # FIXME certificate verification
    r = requests.get("<data_storage>" +
                     data_ref + parameters,
                     headers={"X-Auth-Token": ST}, verify=cert)

    return r.json()


def retrieve_reg(ST, cert, filter_path=None, parameters=[]):

    if parameters:
        parameters = '?' + '&'.join(parameters)
    else:
        parameters = ""

    # FIXME certificate verification
    r = requests.get("<data_storage_registry>" +
                     filter_path + parameters,
                     headers={"X-Auth-Token": ST}, verify=cert)

    return r.json()


def update_data(data_df, page, ST, cert, uri, start, end, e_name):

    parameters = ["page=" + str(page), "per_page=100",
                  "start=" + start, "end=" + end, "sort=asc"]

    data_page = retrieve_data(ST, cert, uri, parameters)

    data = data_page["data"]["e"]

    if data:
        firstDate = dt.datetime.fromtimestamp(data[0]["t"]).strftime("%Y-%m-%d %H:%M:%S")
        lastDate = dt.datetime.fromtimestamp(data[-1]["t"]).strftime("%Y-%m-%d %H:%M:%S")
        print("Page", page, ": from", firstDate, "to", lastDate)

        df = pd.DataFrame.from_dict(data)
        df.columns = ["n", "t", "Unit", "PeriodValue"]
        df["Date"] = df["t"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%d-%m-%Y"))
        df["StartTime"] = df["t"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%H:%M"))
        df["Duration"] = int(30)
        df["TotalValue"] = 0.
        df["Meter"] = ""
        df["Name"] = e_name
        df["SerialNumber"] = ""
        df["Register"] = ""

        df = df[data_df.columns]
        data_df = pd.concat([data_df, df])

    return data_df
