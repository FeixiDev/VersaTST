import sys
import yaml
import re
import json
import threading
import queue
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

	namespace = "default"
	failed_post_scenarios = ""
	go_meter_pod = ""
	lins_blkpvc_file = scenarios_list[0][0]
	gomet_pod_file = scenarios_list[1][0]
	stor_file = scenarios_list[2][0]
	write_q = queue.Queue(maxsize = 1)

	stor_config = utils.ConfFile(stor_file)
	kind = stor_config.get_kind()
	times = int(stor_config.get_number_of_times())

	versa_con = control.IscsiTest(stor_config)

	pvc_resoure = kubecli.create_pvc(lins_blkpvc_file)
	time.sleep(20)
	
	with open(path.join(path.dirname(__file__), gomet_pod_file)) as f:
		gomet_pod_config = yaml.safe_load(f)
		metadata_config = gomet_pod_config["metadata"]
		go_meter_pod = metadata_config.get("name", "")
		kubecli.create_pod_spof(gomet_pod_config, namespace,lins_blkpvc_file, 120)

	time.sleep(2)


	err = versa_con.ckeck_drbd_status_spof(pvc_resoure, False)
	if not err:	
		err = versa_con.check_drbd_crm_res(pvc_resoure, False)
	if err:
		clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)
		exit(1)	

	# err = versa_con.ckeck_drbd_status_spof(pvc_resoure, False)
	# if err:
	# 	clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)
	# 	exit(1)

	left_times = times
	while(left_times):
		down = False
		utils.prt_log('', "Times %d: For single failure, Go-meter start to write" % (times - left_times),0)	
		threading.Thread(target=gometer_write, args=(go_meter_pod, write_q)).start()
		if kind == "node_down":
			versa_con.down_node()
			down = True
		elif kind == "interface_down":
			versa_con.change_node_interface(False)
		elif kind == "switch_port_down":
			versa_con.change_switch_port(False)
		elif kind == "hand_operation":
			utils.prt_log('', "Go-meter start to write",0)
		utils.prt_log('', "Go-meter start to write",0)
		err = write_q.get()
		if err:
			utils.prt_log('', "Go meter write failed",0)
			versa_con.get_log(down)
			clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)
			exit(1)			

		err = versa_con.ckeck_drbd_status_spof(pvc_resoure, down)
		if not err:	
			err = versa_con.check_drbd_crm_res(pvc_resoure, down)
		if err:
			clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)		
			exit(1)

		# err = versa_con.ckeck_drbd_status_spof(pvc_resoure, down)
		# if err:
		# 	clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)
		# 	exit(1)

		utils.prt_log('', "Go-meter start to compare",0)
		command = "cd /go/src/app;./main compare"
		response = kubecli.exec_cmd_in_pod(command, go_meter_pod, namespace)
		utils.prt_log('', "\n" + str(response),0)

		if not "Finish" in response:
			utils.prt_log('', "Go meter compare failed",0)
			if kind == "interface_down":
				versa_con.change_node_interface(True)
			elif kind == "switch_port_down":
				versa_con.change_switch_port(True)
			versa_con.get_log(down)
			clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)
			exit(1)

		utils.prt_log('', "Times %d:For fix single failure, Go-meter start to write" % (times - left_times),0)
		threading.Thread(target=gometer_write, args=(go_meter_pod, write_q)).start()

		if kind == "interface_down":
			versa_con.change_node_interface(True)
		elif kind == "switch_port_down":
			versa_con.change_switch_port(True)
		elif kind == "hand_operation":
			utils.prt_log('', "Please do hand operation...",0)

		down = False
		utils.prt_log('', "Go-meter is writing, wait...",0)
		err = write_q.get()
		if err:
			utils.prt_log('', "Go meter write failed",0)
			versa_con.get_log(down)
			clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)
			exit(1)		

		err = versa_con.ckeck_drbd_status_spof(pvc_resoure, down)
		if not err:	
			err = versa_con.check_drbd_crm_res(pvc_resoure, down)
		if err:
			clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)		
			exit(1)
		# err = versa_con.ckeck_drbd_status_spof(pvc_resoure, down)
		# if err:
		# 	clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)
		# 	exit(1)
		utils.prt_log('', "Go-meter start to compare",0)
		command = "cd /go/src/app;./main compare"
		response = kubecli.exec_cmd_in_pod(command, go_meter_pod, namespace)
		utils.prt_log('', "\n" + str(response),0)

		if not "Finish" in response:
			utils.prt_log('', "Go meter compare failed",0)
			versa_con.get_log(down)
			clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)
			exit(1)
		left_times = left_times - 1

	clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file)


def runtst(scenarios_list, config):
	namespace = "default"
	failed_post_scenarios = ""
	#for app_config in scenarios_list:

	lins_blkpvc_file = scenarios_list[0][0]
	stor_file = scenarios_list[2][0]
	gomet_pod_file = scenarios_list[1][0]

	stor_config = utils.ConfFile(stor_file)

	versa_con = control.IscsiTest(stor_config)
	versa_con.change_switch_port(False)
	print(60000)
	time.sleep(60)
	versa_con.change_switch_port(True)


def clear_pvc_and_pod(go_meter_pod,namespace,lins_blkpvc_file):
	kubecli.delete_pod(go_meter_pod, namespace)
	kubecli.delete_pvc(lins_blkpvc_file)



def gometer_write(pod_name, write_q):

	command = "cd /go/src/app;./main write"
	response = kubecli.exec_cmd_in_pod(command, pod_name, "default")
	utils.prt_log('', "\n" + str(response),0)
	if "Finish" in response:
		write_q.put(0)
	else:
		write_q.put(1)













