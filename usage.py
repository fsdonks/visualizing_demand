#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 18:21:38 2021

@author: craig
"""
import pandas as pd
import sys
import by_demandgroup as dep
import openpyxl
from functools import reduce

def load_trends(path):
    df=pd.read_csv(path, sep="\t") 
    return df

runs = {'without-peak-hold': "/home/craig/runs/rand-runs-demand-trends/base-testdata-v7/DemandTrends.txt",
        'with-peak-hold': {'max_path': '/home/craig/runs/visualizing_demand/computed_maxes.xlsx',
                          'run_info': {"A": "/home/craig/runs/rand-runs-demand-trends/base-testdata-v7/DemandTrends.txt",
        ##one SRC
        "B": "/home/craig/runs/test-run/testdata-v7-bog/DemandTrends.txt"}
        }}

runs2 = {"A": "/home/craig/runs/rand-runs-demand-trends/base-testdata-v7/DemandTrends.txt",
        ##one SRC
        "B": "/home/craig/runs/test-run/testdata-v7-bog/DemandTrends.txt"}

def load_maxes(max_path):
    """Given the path to a max workbook which has two sheets:"""
    maxes=pd.read_excel(max_path, "by_src")
    maxes['demand_name'] = maxes['demand_name'].astype(str)
    maxes=maxes.set_index('SRC')
    peak_map=maxes['demand_name'].to_dict()
    wb = openpyxl.reader.excel.load_workbook(max_path)
    ws=wb['default']
    default_max=str(ws['A1'].value)
    return peak_map, default_max

def min_score_demand_peak(row, peak_map, default_max):
    return peak_map.get(row['SRC'], default_max)

def combine_runs(runs_dict, max_path=None):
    if max_path is not None:
        peak_map, default_max=load_maxes(max_path)
    else:
        run_name =  list(runs_dict)[0]
        peak_map={} 
        default_max=run_name
    combined_data = pd.DataFrame()
    for run_name, path in runs_dict.items():
        df=load_trends(path)
        df['max_demand']=df.apply(lambda row: min_score_demand_peak(row, peak_map, default_max), axis=1)
        df=df[run_name==df['max_demand']]
        df=dep.lerp_demand_trends(df)
        combined_data = combined_data.append(df)
    return combined_data

def check_run_args(run_seq):
    return_dict={}
    """Check to see whether run_seq is a dict of where keys are the run names and values are
    either max_dicts for combined runs or just a path to a run.  If run_seq values are max_dicts,
    then do nothing.  If it is just a path to run, turn it into a max_dict."""
    for run_name, run_item in run_seq.items():
        if type(run_item) is dict:
            ##run_item is already a max_dict
            return_dict[run_name]=run_item
        else:
            ##run_item is just a path to a single run.
            new_dict={'max_path': None,
                      'run_info': {"random_name": run_item}}
            return_dict[run_name]=new_dict
    return return_dict

def merge_fill(left, right):
    left_run_name, left_fill_table = left
    right_run_name, right_fill_table = right
    res = pd.merge(left_fill_table,right_fill_table,on="DemandGroup", how='outer', suffixes=("_"+left_run_name, "_"+right_run_name))
    return res

def results_pdf(fill_table, image_list, out_path):
    hold_table=out_path+"met_table.jpg"
    dep.dataframe_to_image(fill_table, hold_table)
    image_list.append(hold_table)
    pdf1_filename=out_path+"out.pdf"
    dep.images_to_pdf(image_list, pdf1_filename)
        
def delta_table(run_seq, out_path):
    """Given a run_seq, which is a dict of where keys are the run names and values are
    either max_dicts for combined runs or just a path to a run.  Compute a delta table of % demand met for each combined run.""" 
    first_run_name=list(run_seq.keys())[0]
    last_run_name=list(run_seq.keys())[-1]
    max_dicts = check_run_args(run_seq)
    fill_list=[]
    image_list=[]
    grid_list=[]
    for run_name, max_dict in max_dicts.items():
        trends = combine_runs(max_dict['run_info'], max_dict['max_path'])
        sand_chart_path= out_path+run_name+".jpg"
        image_list.append(sand_chart_path)
        demand_fill_table, grid=dep.process_trends(trends, sand_chart_path)
        grid_list.append(grid)
        fill_list.append([run_name, demand_fill_table])
    df_merged = reduce(merge_fill, fill_list)
    df_merged["%met_increase"]=df_merged["%_met_"+last_run_name]-df_merged["%_met_"+first_run_name]
    y_lim_max=max(map(lambda grid: grid.axes[0].get_ylim()[1], grid_list))
    x_lim_max=max(map(lambda grid: grid.axes[0].get_xlim()[1], grid_list))
    
    for grid_num in range(len(grid_list)):
        grid=grid_list[grid_num]
        grid.set(ylim=(0, y_lim_max))
        grid.set(xlim=(0, x_lim_max))
        grid.savefig(image_list[grid_num])
    results_pdf(df_merged, image_list, out_path)
    
def add_periods(DemandTrends, m4_wkbk_path):
    periods=pd.read_excel(m4_wkbk_path, sheet_name = "PeriodRecords")
    bins=list(periods['FromDay'].map(lambda x: x-1))
    bins.append(sys.maxsize)
    labels=periods['Name']
    DemandTrends['periods']=pd.cut(x=DemandTrends['t'], bins=bins, labels=labels)
    
#add_periods(load_trends("/home/craig/runs/big_test/base-testdata-v7/DemandTrends.txt"), "/home/craig/runs/big_test/base-testdata-v7.xlsx")

delta_table(runs, "/home/craig/runs/visualizing_demand/")