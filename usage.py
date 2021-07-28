#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 18:21:38 2021

@author: craig
"""
import pandas as pd
import sys
import by_demandgroup as dep

def load_tab(path):
    return pd.read_csv(path, sep="\t")

no_hold_path="/home/craig/runs/rand-runs-demand-trends/base-testdata-v7/DemandTrends.txt"
hold_path="/home/craig/runs/big_test/base-testdata-v7/DemandTrends.txt"
no_hold_trends=load_tab(no_hold_path)
hold_trends=load_tab(hold_path)
out_root= "/home/craig/runs/visualizing_demand/"
no_hold_image= out_root+"no_peak_hold.jpg"
no_holds=dep.process_trends(no_hold_trends, no_hold_image)
hold_image=out_root+"yes_peak_hold.jpg"
holds=dep.process_trends(hold_trends, hold_image)
combined=pd.merge(no_holds, holds, on="DemandGroup", how="outer", suffixes=("_no_hold", "_hold"))
combined["%met_increase"]=combined["%_met_no_hold"]-combined["%_met_hold"]
print(combined)

def add_periods(DemandTrends, m4_wkbk_path):
    periods=pd.read_excel(m4_wkbk_path, sheet_name = "PeriodRecords")
    bins=list(periods['FromDay'].map(lambda x: x-1))
    bins.append(sys.maxsize)
    print(bins)
    labels=periods['Name']
    DemandTrends['periods']=pd.cut(x=DemandTrends['t'], bins=bins, labels=labels)
    print(DemandTrends.head())
    
add_periods(load_tab("/home/craig/runs/big_test/base-testdata-v7/DemandTrends.txt"), "/home/craig/runs/big_test/base-testdata-v7.xlsx")

hold_table=out_root+"met_table.jpg"
dep.dataframe_to_image(combined, hold_table)
im_list = [no_hold_image, hold_image, hold_table]

pdf1_filename=out_root+"out.pdf"
dep.images_to_pdf(im_list, pdf1_filename)