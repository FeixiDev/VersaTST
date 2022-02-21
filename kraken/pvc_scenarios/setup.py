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




def run(scenarios_list, config):

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

	t_config = scenarios_list[2][0]
	pvc_scenario.run(t_config, config)
	time.sleep(5)

	kubecli.delete_pod(ubuntu_pod, namespace)
	kubecli.delete_pvc(pvc_config)

