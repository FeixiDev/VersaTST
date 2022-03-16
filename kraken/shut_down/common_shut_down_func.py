#!/usr/bin/env python

import sys
import yaml
import logging
import time
import re
import json
from os import path
from multiprocessing.pool import ThreadPool
import kraken.cerberus.setup as cerberus
import kraken.kubernetes.client as kubecli
import kraken.post_actions.actions as post_actions
from kraken.node_actions.aws_node_scenarios import AWS
from kraken.node_actions.openstack_node_scenarios import OPENSTACKCLOUD
from kraken.node_actions.az_node_scenarios import Azure
from kraken.node_actions.gcp_node_scenarios import GCP

import sshv.utils as utils
import sshv.log as log
import sshv.control as control




def run11(scenarios_list, config):

    config_file = scenarios_list[0][0]

    scenario_config = utils.ConfFile(config_file)
    times = int(scenario_config.get_number_of_times())

    k8s_con = control.K8sNodes(scenario_config)

    left_times = times
    while(left_times): 
        logging.info("Times %d: Start shut down k8s cluster", times - left_times)
        #k8s_con.down_nodes()
        logging.info("Has shut down cluster, wait to reboot")
        time.sleep(600)
        utils.prt_log('', f"Start to check cluster",0)
        nodes_status = kubecli.monitor_nodes()
        if(nodes_status[0]  == False):
            utils.prt_log('', f"Node status is not normal",1)
            exit(1)
        err = kubecli.check_all_pods()
        if err:
            utils.prt_log('', f"Pod status is not normal",1)
            exit(1)
        left_times = left_times - 1


def run(scenarios_list, config):

    config_file = scenarios_list[0][0]
    
    scenario_config = utils.ConfFile(config_file)
    times = int(scenario_config.get_number_of_times())
    print(kubecli.check_all_pods())

    #print(kubecli.monitor_nodes())
    #k8s_con = control.K8sNodes(scenario_config)











