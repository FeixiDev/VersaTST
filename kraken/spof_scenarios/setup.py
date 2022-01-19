import sys
import yaml
import re
import json
import logging
import threading
import time
from os import path
import kraken.cerberus.setup as cerberus
import kraken.kubernetes.client as kubecli
import kraken.invoke.command as runcommand
import kraken.pvc.pvc_scenario as pvc_scenario
import sshv.utils as utils
import sshv.log as log
import sshv.control as control


def run(scenarios_list, config):

	namespace = "kraken"
	failed_post_scenarios = ""
	go_meter_pod = ""
	lins_blkpvc_file = scenarios_list[0][0]
	gomet_pod_file = scenarios_list[1][0]
	stor_file = scenarios_list[2][0]
	write_wait = threading.Event()
	utils._init()
	logger = log.Log()
	utils.set_logger(logger)
	stor_config = utils.ConfFile(stor_file)
	kind = stor_config.get_kind()
	times = int(stor_config.get_number_of_times())

	pvc_resoure = kubecli.create_pvc(lins_blkpvc_file)
	time.sleep(20)
	
	with open(path.join(path.dirname(__file__), gomet_pod_file)) as f:
		gomet_pod_config = yaml.safe_load(f)
		metadata_config = gomet_pod_config["metadata"]
		go_meter_pod = metadata_config.get("name", "")
		kubecli.create_pod(gomet_pod_config, namespace, 120)

	time.sleep(2)

	versa_con = control.IscsiTest(stor_config)

	err = versa_con.ckeck_drbd_status_spof(pvc_resoure, False)
	if not err:	
		err = versa_con.check_drbd_crm_res(pvc_resoure, False)
	if err:
		clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)
		exit(1)	

	left_times = times
	while(left_times):
		down = False	
		logging.info("Times %d: Go-meter start to write", times - left_times)
		threading.Thread(target=gometer_write, args=(go_meter_pod, write_wait)).start()
		if kind == "node_down":
			versa_con.down_node()
			down = True
		elif kind == "interface_down":
			versa_con.change_node_interface(False)
		elif kind == "switch_port_down":
			versa_con.change_switch_port(False)
		elif kind == "hand_operation":
			logging.info("Please do hand operation...")

		logging.info("Go-meter is writing, wait...")
		write_wait.wait()
		write_wait.clear()

		err = versa_con.ckeck_drbd_status_spof(pvc_resoure, down)
		if not err:	
			err = versa_con.check_drbd_crm_res(pvc_resoure, down)
		if err:
			clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)		
			exit(1)

		logging.info("Go-meter start to compare")
		command = "cd /go/src/app;./main compare"
		response = kubecli.exec_cmd_in_pod(command, go_meter_pod, namespace)
		logging.info("\n" + str(response))

		if kind == "interface_down":
			versa_con.change_node_interface(True)
		elif kind == "switch_port_down":
			versa_con.change_switch_port(True)

		time.sleep(10)
		if not "Finish" in response:
			utils.prt_log('', f"Go meter compare failed",1)
			versa_con.get_log(down)
			clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)
			exit(1)
		left_times = left_times - 1

	clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)


def clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file):
	kubecli.delete_pod(go_meter_pod, namespace)
	kubecli.delete_pvc(lins_blkpvc_file)

def runc(scenarios_list, config):
	namespace = "kraken"
	failed_post_scenarios = ""
	#for app_config in scenarios_list:

	lins_blkpvc_file = scenarios_list[0][0]
	pvc_resoure = kubecli.create_pvc(lins_blkpvc_file)
	print(pvc_resoure_name)
	time.sleep(30)

	gomet_pod_file = scenarios_list[1][0]
	with open(path.join(path.dirname(__file__), gomet_pod_file)) as f:
		gomet_pod_config = yaml.safe_load(f)
		kubecli.create_pod(gomet_pod_config, namespace, 120)



def rund(scenarios_list, config):
	namespace = "kraken"
	failed_post_scenarios = ""
	#for app_config in scenarios_list:

	lins_blkpvc_file = scenarios_list[0][0]

	gomet_pod_file = scenarios_list[1][0]


	# with open(path.join(path.dirname(__file__), gomet_pod_file)) as f:
	# 	gomet_pod_config = yaml.full_load(f)
	# 	scenario_config = gomet_pod_config["metadata"]
	# 	pod_name = scenario_config.get("name", "")
	# 	kubecli.delete_pod(pod_name, namespace)

	kubecli.delete_pvc(lins_blkpvc_file)


def gometer_write(pod_name,write_wait):

	command = "cd /go/src/app;./main write"
	response = kubecli.exec_cmd_in_pod(command, pod_name, "kraken")
	logging.info("\n" + str(response))
	write_wait.set()













