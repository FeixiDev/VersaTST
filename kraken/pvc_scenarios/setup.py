import yaml
import kraken.kubernetes.client as kubecli
from os import path

def run(scenarios_list, config):
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

	# t_config = scenarios_list[2][0]
	# pvc_scenario.run(t_config, config)
	# time.sleep(5)

	# kubecli.delete_dep(dep_config)
	# time.sleep(23)
	# kubecli.delete_pvc(pvc_config)

