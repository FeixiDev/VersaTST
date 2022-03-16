#!/usr/bin/env python

import os
import sys
import yaml
import logging
import optparse
import pyfiglet
import uuid
import time
import kraken.kubernetes.client as kubecli
import kraken.invoke.command as runcommand
import kraken.litmus.common_litmus as common_litmus
import kraken.time_actions.common_time_functions as time_actions
import kraken.performance_dashboards.setup as performance_dashboards
import kraken.pod_scenarios.setup as pod_scenarios
import kraken.namespace_actions.common_namespace_functions as namespace_actions
import kraken.shut_down.common_shut_down_func as shut_down
import kraken.node_actions.run as nodeaction
import kraken.kube_burner.client as kube_burner
import kraken.zone_outage.actions as zone_outages
import kraken.application_outage.actions as application_outage
import kraken.spof_scenarios.setup as spof_scenarios
import kraken.performance_scenarios.VersaTST_performance as per_scenarios
import kraken.performance_scenarios.Performance_scenarios as scenarios
import kraken.spof_pvc_scenarios.setup as spof_pvc_scenarios
import kraken.pvc_scenarios.setup as pvc_scenarios
import server as server


import sshv.utils as utils
import sshv.log as log
import linstorclient.client as linstorcli

def publish_kraken_status(status):
    with open("/tmp/kraken_status", "w+") as file:
        file.write(str(status))


# Main function
def main(cfg):
    # Start kraken
    print(pyfiglet.figlet_format("VersaTST"))

    check_log_dir = scenarios.Check_log_dir()
    # Parse and read the config
    if os.path.isfile(cfg):

        with open(cfg, "r") as f:
            config = yaml.full_load(f)
        global kubeconfig_path, wait_duration
        distribution = config["kraken"].get("distribution")
        if 'kubernetes' in str(distribution):
            kubeconfig_path = config["kraken"].get("kubeconfig_path", "")
            chaos_scenarios = config["kraken"].get("chaos_scenarios", [])
            publish_running_status = config["kraken"].get("publish_kraken_status", False)
            port = config["kraken"].get("port", "8081")
            run_signal = config["kraken"].get("signal_state", "RUN")
            litmus_version = config["kraken"].get("litmus_version", "v1.9.1")
            litmus_uninstall = config["kraken"].get("litmus_uninstall", False)
            wait_duration = config["tunings"].get("wait_duration", 60)
            iterations = config["tunings"].get("iterations", 1)
            daemon_mode = config["tunings"].get("daemon_mode", False)
            deploy_performance_dashboards = config["performance_monitoring"].get("deploy_dashboards", False)
            dashboard_repo = config["performance_monitoring"].get(
                "repo", "https://github.com/cloud-bulldozer/performance-dashboards.git"
            )  # noqa
            capture_metrics = config["performance_monitoring"].get("capture_metrics", False)
            kube_burner_url = config["performance_monitoring"].get(
                "kube_burner_binary_url",
                "https://github.com/cloud-bulldozer/kube-burner/releases/download/v0.9.1/kube-burner-0.9.1-Linux-x86_64.tar.gz",  # noqa
            )
            config_path = config["performance_monitoring"].get("config_path", "config/kube_burner.yaml")
            metrics_profile = config["performance_monitoring"].get("metrics_profile_path", "config/metrics-aggregated.yaml")
            prometheus_url = config["performance_monitoring"].get("prometheus_url", "")
            prometheus_bearer_token = config["performance_monitoring"].get("prometheus_bearer_token", "")
            run_uuid = config["performance_monitoring"].get("uuid", "")
            enable_alerts = config["performance_monitoring"].get("enable_alerts", False)
            alert_profile = config["performance_monitoring"].get("alert_profile", "")

            # Initialize clients
            if not os.path.isfile(kubeconfig_path):
                utils.prt_log('', "Cannot read the kubeconfig file at %s, please check" % kubeconfig_path,0)
                #logging.error("Cannot read the kubeconfig file at %s, please check" % kubeconfig_path)
                sys.exit(1)
            utils.prt_log('', "Initializing client to talk to the Kubernetes cluster",0)
            #logging.info("Initializing client to talk to the Kubernetes cluster")
            os.environ["KUBECONFIG"] = str(kubeconfig_path)
            kubecli.initialize_clients(kubeconfig_path)

            # find node kraken might be running on
            kubecli.find_kraken_node()

            # Set up kraken url to track signal
            if not 0 <= int(port) <= 65535:
                utils.prt_log('', "Using port 8081 as %s isn't a valid port number" % (port),0)
                #logging.info("Using port 8081 as %s isn't a valid port number" % (port))
                port = 8081
            address = ("0.0.0.0", port)

            # If publish_running_status is False this should keep us going in our loop below
            if publish_running_status:
                server_address = address[0]
                port = address[1]
                utils.prt_log('', "Publishing kraken status at http://%s:%s" % (server_address, port),0)
                #logging.info("Publishing kraken status at http://%s:%s" % (server_address, port))
                server.start_server(address)
                publish_kraken_status(run_signal)

            # Cluster info
            # logging.info("Fetching cluster info")
            # cluster_version = runcommand.invoke("kubectl get clusterversion", 60)
            # cluster_info = runcommand.invoke(
            #     "kubectl cluster-info | awk 'NR==1' | sed -r " "'s/\x1B\[([0-9]{1,3}(;[0-9]{1,2})?)?[mGK]//g'", 60
            # )  # noqa
            # logging.info("\n%s%s" % (cluster_version, cluster_info))

            # Deploy performance dashboards
            if deploy_performance_dashboards:
                performance_dashboards.setup(dashboard_repo)

            # Generate uuid for the run
            if run_uuid:
                utils.prt_log('', "Using the uuid defined by the user for the run: %s" % run_uuid,0)
                #logging.info("Using the uuid defined by the user for the run: %s" % run_uuid)
            else:
                run_uuid = str(uuid.uuid4())
                utils.prt_log('', "Generated a uuid for the run: %s" % run_uuid,0)
                #logging.info("Generated a uuid for the run: %s" % run_uuid)

            # Initialize the start iteration to 0
            iteration = 0

            # Set the number of iterations to loop to infinity if daemon mode is
            # enabled or else set it to the provided iterations count in the config
            if daemon_mode:
                utils.prt_log('', "Daemon mode enabled, kraken will cause chaos forever\n",0)
                utils.prt_log('', "Ignoring the iterations set",0)
                #logging.info("Daemon mode enabled, kraken will cause chaos forever\n")
                #logging.info("Ignoring the iterations set")
                iterations = float("inf")
            else:
                utils.prt_log('', "Daemon mode not enabled, will run through %s iterations\n" % str(iterations),0)
                #logging.info("Daemon mode not enabled, will run through %s iterations\n" % str(iterations))
                iterations = int(iterations)

            failed_post_scenarios = []
            litmus_installed = False

            # Capture the start time
            start_time = int(time.time())

            # Loop to run the chaos starts here
            while int(iteration) < iterations and run_signal != "STOP":
                # Inject chaos scenarios specified in the config
                utils.prt_log('', "Executing scenarios for iteration " + str(iteration),0)
                #logging.info("Executing scenarios for iteration " + str(iteration))

                if chaos_scenarios:
                    for scenario in chaos_scenarios:
                        if publish_running_status:
                            run_signal = server.get_status(address)
                        if run_signal == "PAUSE":
                            while publish_running_status and run_signal == "PAUSE":
                                utils.prt_log('', "Pausing Kraken run, waiting for %s seconds and will re-poll signal"
                                    % str(wait_duration),0)

                                time.sleep(wait_duration)
                                run_signal = server.get_status(address)
                        if run_signal == "STOP":
                            utils.prt_log('', "Received STOP signal; ending Kraken run",0)
                            #logging.info("Received STOP signal; ending Kraken run")
                            break
                        scenario_type = list(scenario.keys())[0]
                        scenarios_list = scenario[scenario_type]
                        if scenarios_list:
                            # Inject pod chaos scenarios specified in the config
                            if scenario_type == "pod_scenarios":
                                utils.prt_log('', "Running pod scenarios",0)
                                #logging.info("Running pod scenarios")
                                failed_post_scenarios = pod_scenarios.run(
                                    kubeconfig_path, scenarios_list, config, failed_post_scenarios, wait_duration
                                )
                            elif scenario_type == "container_scenarios":
                                utils.prt_log('', "Running container scenarios",0)
                                #logging.info("Running container scenarios")
                                failed_post_scenarios = pod_scenarios.container_run(
                                    kubeconfig_path, scenarios_list, config, failed_post_scenarios, wait_duration
                                )

                            # Inject node chaos scenarios specified in the config
                            elif scenario_type == "node_scenarios":
                                utils.prt_log('', "Running node scenarios",0)
                                #logging.info("Running node scenarios")
                                nodeaction.run(scenarios_list, config, wait_duration)

                            # Inject time skew chaos scenarios specified in the config
                            elif scenario_type == "time_scenarios":
                                utils.prt_log('', "Running time skew scenarios",0)
                                #logging.info("Running time skew scenarios")
                                time_actions.run(scenarios_list, config, wait_duration)

                            # Inject litmus based chaos scenarios
                            elif scenario_type == "litmus_scenarios":
                                utils.prt_log('', "Running litmus scenarios",0)
                                #logging.info("Running litmus scenarios")
                                litmus_namespace = "litmus"
                                if not litmus_installed:
                                    # Will always uninstall first
                                    common_litmus.delete_chaos(litmus_namespace)
                                    common_litmus.delete_chaos_experiments(litmus_namespace)
                                    common_litmus.uninstall_litmus(litmus_version, litmus_namespace)
                                    common_litmus.install_litmus(litmus_version, litmus_namespace)
                                    common_litmus.deploy_all_experiments(litmus_version, litmus_namespace)
                                    litmus_installed = True
                                    common_litmus.run(
                                        scenarios_list, config, litmus_uninstall, wait_duration, litmus_namespace,
                                    )

                            # Inject cluster shutdown scenarios
                            elif scenario_type == "cluster_shut_down_scenarios":
                                shut_down.run(scenarios_list, config)

                            # Inject namespace chaos scenarios
                            elif scenario_type == "namespace_scenarios":
                                utils.prt_log('', "Running namespace scenarios",0)
                                #logging.info("Running namespace scenarios")
                                namespace_actions.run(
                                    scenarios_list, config, wait_duration, failed_post_scenarios, kubeconfig_path
                                )
                                
                            # Inject zone failures
                            elif scenario_type == "zone_outages":
                                utils.prt_log('', "Inject zone outages",0)
                                #logging.info("Inject zone outages")
                                zone_outages.run(scenarios_list, config, wait_duration)

                            # Application outages
                            elif scenario_type == "application_outages":
                                utils.prt_log('', "Injecting application outage",0)
                                #logging.info("Injecting application outage")
                                application_outage.run(scenarios_list, config, wait_duration)

                            # PVC scenarios
                            elif scenario_type == "pvc_scenarios":
                                utils.prt_log('', "Running pvc scenario",0)
                                #logging.info("Running pvc scenario")
                                pvc_scenarios.run(scenarios_list, config)

                            elif scenario_type == "spof_pvc_scenarios":
                                logging.info("Running spof pvc scenario")
                                linstorcli.initialize_clients()
                                spof_pvc_scenarios.run(scenarios_list,config)

                            elif scenario_type == "spof_scenarios":
                                utils.prt_log('', "Running spof scenario",0)
                                #logging.info("Running spof scenario")
                                spof_scenarios.run(scenarios_list, config)
                                #spof_scenarios.down_interface()

                iteration += 1

            # Capture the end time
            end_time = int(time.time())

            # Capture metrics for the run
            if capture_metrics:
                utils.prt_log('', "Capturing metrics",0)
                #logging.info("Capturing metrics")
                kube_burner.setup(kube_burner_url)
                kube_burner.scrape_metrics(
                    distribution,
                    run_uuid,
                    prometheus_url,
                    prometheus_bearer_token,
                    start_time,
                    end_time,
                    config_path,
                    metrics_profile,
                )

            # Check for the alerts specified
            if enable_alerts:
                utils.prt_log('', "Alerts checking is enabled",0)
                #logging.info("Alerts checking is enabled")
                kube_burner.setup(kube_burner_url)
                if alert_profile:
                    kube_burner.alerts(
                        distribution, prometheus_url, prometheus_bearer_token, start_time, end_time, alert_profile,
                    )
                else:
                    utils.prt_log('', "Alert profile is not defined",0)
                    #logging.error("Alert profile is not defined")
                    sys.exit(1)

            if litmus_uninstall and litmus_installed:
                common_litmus.delete_chaos(litmus_namespace)
                common_litmus.delete_chaos_experiments(litmus_namespace)
                common_litmus.uninstall_litmus(litmus_version, litmus_namespace)

            if failed_post_scenarios:
                utils.prt_log('', "Post scenarios are still failing at the end of all iterations",0)
                #logging.error("Post scenarios are still failing at the end of all iterations")
                sys.exit(1)


            run_dir = os.getcwd() + "/kraken.report"
            utils.prt_log('', "Successfully finished running Kraken. UUID for the run: %s. Report generated at %s. Exiting"
                % (run_uuid, run_dir),0)
            # logging.info(
            #     "Successfully finished running Kraken. UUID for the run: %s. Report generated at %s. Exiting"
            #     % (run_uuid, run_dir)
            # )
        else:
            chaos_scenarios = config["kraken"].get("chaos_scenarios", [])
            for scenario in range(len(chaos_scenarios)):
                scenario_type = list(chaos_scenarios[scenario].keys())[0]
                scenarios_list = list(chaos_scenarios[scenario].values())[0]
                if scenario_type == "down_nic_scenarios":
                    signal = True
                    scenarios_list = list(chaos_scenarios[1].values())[0]
                    #per_scenarios.run(scenarios_list,config,signal=signal)
                    sys.exit(1)

                if scenario_type == "performance_scenarios":
                    per_scenarios.run(scenarios_list,config)
    else:
        utils.prt_log('', "Cannot find a config at %s, please check" % (cfg),0)
        #logging.error("Cannot find a config at %s, please check" % (cfg))
        sys.exit(1)


if __name__ == "__main__":
    # Initialize the parser to read the config
    parser = optparse.OptionParser()
    parser.add_option(
        "-c", "--config", dest="cfg", help="config location", default="config/config.yaml",
    )
    (options, args) = parser.parse_args()
    utils._init()
    logger = log.Log()
    utils.set_logger(logger)

    if options.cfg is None:
        utils.prt_log('', "Please check if you have passed the config",0)
        #logging.error("Please check if you have passed the config")
        sys.exit(1)
    else:
        main(options.cfg)
