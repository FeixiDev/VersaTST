import sys
import yaml
import re
import json
import logging
import time
from os import path
import kraken.cerberus.setup as cerberus
import kraken.kubernetes.client as kubecli
import kraken.invoke.command as runcommand
import kraken.pvc.pvc_scenario as pvc_scenario
from os import path

import datetime







def run(scenarios_list, config):
<<<<<<< HEAD:kraken/pvc_demo/setup.py
	# print("start creat_pvc")
	failed_post_scenarios = ""
	pvc_config = scenarios_list[0][0]
	f = open(f'./kraken{pvc_config}')
	pvc = yaml.safe_load(f)
	f.close()

	# create
	# t1 = datetime.datetime.now()
	# for i in range(0,3):
	# 	pvc['metadata']['name'] = f'pvc-test{i}'
	# 	kubecli.create_pvc_(pvc,"kraken")
	# t2 = datetime.datetime.now()
	# print("cost:",t2-t1)


	# delete
	# for i in range(0,100):
	# 	name = f'pvc-test{i}'
	# 	kubecli.delete_pvc_(name,"kraken")


	# list 
	print(kubecli.get_all_pvc_status('kraken'))


	# print(kubecli.get_pvc_status('pvc-test1','kraken'))





#demo
	# pvc_config = scenarios_list[0][0]
	# kubecli.create_pvc(pvc_config)
	# time.sleep(30)

	# dep_config = scenarios_list[1][0]
	# kubecli.create_dep(dep_config)
	# time.sleep(55)
=======

	print("start creat_pvc")
	failed_post_scenarios = ""
	ubuntu_pod = ""
	namespace = "default"
	#for app_config in scenarios_list:
	pvc_config = scenarios_list[0][0]
	kubecli.create_pvc(pvc_config)
	time.sleep(20)

	dep_config = scenarios_list[1][0]
	with open(path.join(path.dirname(__file__), dep_config)) as f:
		pod_config = yaml.safe_load(f)
		metadata_config = pod_config["metadata"]
		ubuntu_pod = metadata_config.get("name", "")
		kubecli.create_pod_spof(pod_config, namespace,pvc_config, 120)

	time.sleep(2)
>>>>>>> 91aa91af40b42b2681b167f6e727571ff7516596:kraken/pvc_scenarios/setup.py

	# t_config = scenarios_list[2][0]
	# pvc_scenario.run(t_config, config)
	# time.sleep(5)

<<<<<<< HEAD:kraken/pvc_demo/setup.py
	# kubecli.delete_dep(dep_config)
	# time.sleep(23)
	# kubecli.delete_pvc(pvc_config)
=======
	kubecli.delete_pod(ubuntu_pod, namespace)
	kubecli.delete_pvc(pvc_config)
>>>>>>> 91aa91af40b42b2681b167f6e727571ff7516596:kraken/pvc_scenarios/setup.py

