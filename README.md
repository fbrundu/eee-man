# eee

## Dependencies

* Python3
* CherryPy
* pandas
* pymatbridge
* xlrd
* pyzmq
* paho-mqtt
* requests
* scipy

## Start the service

    python3 eee.py

## Setting the configuration file

The configuration file must be saved in the directory `conf/` as `conf.json`.

## Description

The service allows the following methods:

* GET
* POST

Currently, the following actions are implemented:

* ping (GET)
* sched (GET) - retrieve results of a simulation as JSON response. Parameters:
    * reqid - the ID of the simulation
* sched (POST) - start a new simulation to get schedule for tomorrow
