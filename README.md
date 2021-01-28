# District Heating Simulator - Manchester version

This repository is part of a collection, see also:
- BIM Service Provider - Context layer: https://github.com/fbrundu/dimc
- BIM Service Provider - Interface layer: https://github.com/fbrundu/bimp
- District Heating Simulator - Turin version https://github.com/fbrundu/eee-trn

Full citation:
- Brundu, Francesco Gavino, et al. "IoT software infrastructure for energy management and simulation in smart cities." IEEE Transactions on Industrial Informatics 13.2 (2016): 832-840.

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
