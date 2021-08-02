#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 18:21:38 2021

@author: craig
"""
import by_demandgroup as dep

runs = {'without-peak-hold': "/home/craig/runs/rand-runs-demand-trends/base-testdata-v7/DemandTrends.txt",
        'with-peak-hold': {'max_path': '/home/craig/runs/visualizing_demand/computed_maxes.xlsx',
                          'run_info': {"A": "/home/craig/runs/rand-runs-demand-trends/base-testdata-v7/DemandTrends.txt",
        ##one SRC
        "B": "/home/craig/runs/test-run/testdata-v7-bog/DemandTrends.txt"}
        }}

runs2 = {"A": "/home/craig/runs/rand-runs-demand-trends/base-testdata-v7/DemandTrends.txt",
        ##one SRC
        "B": "/home/craig/runs/test-run/testdata-v7-bog/DemandTrends.txt"}

#add_periods(load_trends("/home/craig/runs/big_test/base-testdata-v7/DemandTrends.txt"), "/home/craig/runs/big_test/base-testdata-v7.xlsx")

dep.delta_table(runs, "/home/craig/runs/visualizing_demand/")