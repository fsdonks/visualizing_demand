#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 18:21:38 2021

@author: craig
"""
import by_demandgroup as dep
import os

runs = {'without-peak-hold': "/home/craig/runs/rand-runs-demand-trends/base-testdata-v7/DemandTrends.txt",
        'with-peak-hold': {'max_path': '/home/craig/runs/visualizing_demand/computed_maxes.xlsx',
                          'run_info': {"A": "/home/craig/runs/rand-runs-demand-trends/base-testdata-v7/DemandTrends.txt",
        ##one SRC
        "B": "/home/craig/runs/test-run/testdata-v7-bog/DemandTrends.txt"}
        }}

runs2 = {"A": "/home/craig/runs/rand-runs-demand-trends/base-testdata-v7/DemandTrends.txt",
        ##one SRC
        "B": "/home/craig/runs/test-run/testdata-v7-bog/DemandTrends.txt"}

big_run = {"A": "/home/craig/runs/big_test/base-testdata-v7/DemandTrends.txt",}

little_run = {"A": "/home/craig/runs/test-run/testdata-v7-bog/DemandTrends.txt",}

#add_periods(load_trends("/home/craig/runs/big_test/base-testdata-v7/DemandTrends.txt"), "/home/craig/runs/big_test/base-testdata-v7.xlsx")

#dep.delta_table(big_run, "/home/craig/runs/visualizing_demand/")

#In trends, two folders, one for A and one for B. done in Clojure
#assume cuts the same between folders, so first, get a list of folders
#in the directory


#given a directory (with folders for each scenario), make an input map
#where the keys are the names of the trend files and the values are a run-map with max_path and
#run_info is from all folders within trends
#combined trends get outputted after the visual, need to suck these back into r.


def cut_map(trend_path, max_path):
    """Generate the run map to send to delta_table. trend_path should contain only directories, and each directory holds a list of demand trends.  each directory should contain the same number and file names for the demand trends."""
    subfolders = [ f for f in os.scandir(trend_path) if f.is_dir() ]
    first_folder=subfolders[0].path
    res={}
    for f in os.scandir(first_folder):
        upper_dict={}
        run_dict={}
        for run in subfolders:
            #need to figure out how to loop here.
            #just the file name
            run_dict[run.name]=run.path + "/" + f.name
        name = os.path.splitext(f.name)[0]
        upper_dict['max_path']= max_path
        upper_dict['run_info']=run_dict
        res[name]=upper_dict
    return res

max_path = '/home/craig/runs/visualizing_demand/computed_maxes.xlsx'
in_map=cut_map("/home/craig/runs/cut-trends/trends/", max_path)
#dep.delta_table(in_map, "/home/craig/runs/cut-trends/trends/")
trend_path= "/home/craig/runs/cut-trends/trends/"
dep.prep_for_rg_charts(trend_path, 1000, 2000)