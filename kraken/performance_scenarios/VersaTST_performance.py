#  coding: utf-8
import optparse
import pyfiglet
import os
import sys
import yaml
import kraken.performance_scenarios.utils as utils
import kraken.performance_scenarios.log as log
import sqlite3
import kraken.performance_scenarios.basic as basic
import kraken.performance_scenarios.sql_input as sqlin
import kraken.performance_scenarios.sql_select as excel
import kraken.performance_scenarios.sql_chart as sqlchart
import kraken.performance_scenarios.sql_histogram as sqlhis
import kraken.performance_scenarios.sql_deviation as sqldevi
import kraken.performance_scenarios.Performance_scenarios as scenarios



def run(scenarios_list, config,signal=False):
    #check_log_dir = scenarios.Check_log_dir()
    signal_run = signal
    utils._init()
    logger = log.Log()
    utils.set_logger(logger)
    check_file_dir = scenarios.Check_file_dir()
    for i in range(len(scenarios_list)):
        if 'P_sql_config' in str(scenarios_list[i]):
            perforamce_manual()
        else:
            scenarios.Run_test(scenarios_list[i][0],signal=signal_run)



def perforamce_manual():
    basic_fun = basic.Basic_function()
    try:
        basic_fun.sql_print_index()
    except sqlite3.OperationalError:
        print("Please input FIO result text file name and other information in Yaml configuraion for input.py first AND THEN ENTER input in the next question")

    typein = input("What kind of function do you want to use? (view/input/analysis/graph/deviation/manage):")
    if typein == "input":
        sqlin.Run_test_for_main()


    elif typein == "analysis":
        basic_fun.sql_print_index()
        write_excel = excel.write_excel_manual()
        number_of_table = input("How many tables do you want to analyze with? (Enter: many / 2):")
        if number_of_table  == "many":
            write_excel.sql_analysis_output()
        if number_of_table  == "2":
            write_excel.sql_analysis_output_2()
    

    elif typein == "graph":
        basic_fun.sql_print_index()
        graph = input("What kind of graph do you want to create? (Enter: chart / histogram):")
        if graph == "chart":
            chart_fun = sqlchart.graph_chart_manual()
            kind = input("Do you want to create chart with drbd type or readwrite type?(Enter: dt / rw):")
            if kind == "dt":
                chart_fun.sql_graph_output()
            if kind == "rw":
                chart_fun.sql_print_drbd()
                chart_fun.sql_graph_rw()
        if graph == "histogram":
            histogram_fun = sqlhis.graph_histogram_manual()
            histogram_fun.graph_histogram_output()

    
    elif typein == "deviation":
        deviation = input("What kind of deviation do you want to create? (Enter: multiple standards / 1 standard)")
        if deviation == "multiple standards":
            sqldevi.sql_print_standard_drbd()
            sqldevi.sql_pick_standard_values()
            sqldevi.sql_print_example_drbd()
            sqldevi.sql_pick_example_values()
            sqldevi.draw()
        if deviation == "1 standard":
            sqldevi.sql_print_standard_drbd()
            sqldevi.sql_pick_standard_values_1()
            sqldevi.sql_print_example_drbd()
            sqldevi.sql_pick_example_values()
            sqldevi.draw_1standard()


    elif typein == "view":
        basic_fun.view_sql_data()
    

    elif typein == "manage":
        basic_fun.sql_print_index()
        basic_fun.drop_table()
        basic_fun.drop_row()
    

    elif typein not in ["input", "analysis", "graph", "deviation", "view", "manage"]:
        print("Not a vaild keyword. Please Enter again.")


if __name__=='__main__':
    pass







