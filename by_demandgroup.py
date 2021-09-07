#!/usr/bin/env python
# coding: utf-8

#Load the data.
# libraries
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image
import pandas as pd
import sys
import openpyxl
from functools import reduce
import subprocess
import os

def trends_by_demand_type(DemandTrends):
    DemandTrends['TotalFilled']=DemandTrends['TotalFilled']
    DemandTrends["Unmet"]=DemandTrends["TotalRequired"] - DemandTrends["Deployed"]
    DemandTrends["Unmet"]=DemandTrends["Unmet"]+DemandTrends["TotalFilled"]
    alphabetical=sorted(DemandTrends.DemandGroup.unique(), key=str.lower)
    #here, group by interest, then send through:
    return DemandTrends.groupby(['t', 'DemandGroup']).sum().reset_index(), alphabetical


# In[5]:


#Need to do this for a stacked, step-style stacked area chart.
#Facet grid is nice because it makes vertical axis consistent.

def sand_trends_by_demand_group(DemandTrends):
    trends, group_order=trends_by_demand_type(DemandTrends)
    # Create a grid : initialize it
    g = sns.FacetGrid(trends, col='DemandGroup', hue='DemandGroup', col_wrap=4, col_order=group_order)
    # Add the line over the area with the plot function
    g = g.map(plt.plot, 't', 'TotalFilled', drawstyle="steps-post", color='green', lw=.01)
    g = g.map(plt.plot, 't', 'Unmet', drawstyle="steps-post", color='black', lw=.01)
    # Fill the area with fill_between
    g = g.map(plt.fill_between, 't', 'TotalFilled', step='post', color='green', lw=.01).set_titles("{col_name} DemandGroup")
    g = g.map(plt.fill_between, 't', 'Unmet', 'TotalFilled', step='post', color='black', lw=.01).set_titles("{col_name} DemandGroup")
    
    # Control the title of each facet
    g.set_titles("{col_name}")
     
    # Add a title for the whole plot
    plt.subplots_adjust(top=0.92)
    g.fig.suptitle('Fill by Demand Type')
    return g

#Compute % met by demand type and SRC

def compute_fill(DemandTrends):
    DemandTrends["weighted_deployed"] = (DemandTrends["Deployed"]
                                         *DemandTrends["deltaT"])
    DemandTrends["weighted_required"] = (DemandTrends["TotalRequired"] 
                                         *DemandTrends["deltaT"])
    
    return (DemandTrends["weighted_deployed"].sum() /
            DemandTrends["weighted_required"].sum())

def fills_by_demand_group(DemandTrends):
#groupby and then apply
    fills=DemandTrends.groupby(["DemandGroup"]).apply(compute_fill)
    fills=fills.reset_index(name='%_met')
    fills=fills.sort_values(['%_met'])
    return fills

def process_trends(DemandTrends, plot_path):
    grid=sand_trends_by_demand_group(DemandTrends)
    #plt.savefig(plot_path)
    # Show the graph
    #plt.show()
    fills=fills_by_demand_group(DemandTrends)
    return fills, grid

def images_to_pdf(image_paths, filename):
    image_paths = [Image.open(x) for x in image_paths]
    im1=image_paths[0]
    im_list = image_paths[1:]
    im1.save(filename, "PDF" ,resolution=100.0, save_all=True,          append_images=im_list)
    
def dataframe_to_image(df, out_path):
    fig, ax =plt.subplots(figsize=(12,4))
    ax.axis('tight')
    ax.axis('off')
    ax.table(cellText=df.values,colLabels=df.columns,loc='center')
    fig.savefig(out_path)

def add_missing_demand(DemandTrends):
    new_rows=[]
    for key, subframe in DemandTrends:
            init=True
            prev_end=-1
            for index, row in subframe.iterrows():
                if row['t']>prev_end and not init:
                    new_row=dict(zip(subframe.columns, [0]*len(subframe.columns)))
                    new_row['t']=prev_end
                    new_row['SRC']=row['SRC']
                    new_row['DemandGroup']=row['DemandGroup']
                    new_rows.append(new_row)
                init=False
                prev_end=row['t']+row['deltaT']
    return DemandTrends, new_rows

#first, make sure we have a record for every day in DemandTrends
#then 0 out the demand when there is no record for a demandgroup
#deltaT indicates when a demand stops
def lerp_demand_trends(DemandTrends):
    # Groupby src, demand group
    df = DemandTrends.groupby(["DemandGroup", "SRC"])
    df, new_rows = add_missing_demand(df)
    df=df.apply(lambda dframe: dframe)
    df=df.append(new_rows, ignore_index=True)
    return df 

def load_trends(path):
    df=pd.read_csv(path, sep="\t") 
    return df

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
        df=lerp_demand_trends(df)
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
    return [right_run_name, res]

def results_pdf(fill_table, image_list, out_path):
    hold_table=out_path+"met_table.jpg"
    dataframe_to_image(fill_table, hold_table)
    image_list.append(hold_table)
    pdf1_filename=out_path+"out.pdf"
    images_to_pdf(image_list, pdf1_filename)
        
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
        #write out trends to file for R script
        trend_path=out_path+run_name+'_trends.txt'
        trends.to_csv(trend_path, sep ='\t')
        rg_out_name = run_name+"_rg_chart.jpeg"
        subprocess.call(["Rscript", "/home/craig/workspace/visualize-demand/red_green_chart.R", trend_path, rg_out_name, out_path])
        sand_chart_path= out_path+run_name+".jpg"
        image_list.append(sand_chart_path)
        image_list.append(out_path + rg_out_name)
        demand_fill_table, grid=process_trends(trends, sand_chart_path)
        grid_list.append(grid)
        fill_list.append([run_name, demand_fill_table])
    if len(fill_list)==1:
        run_name, demand_fill_table = fill_list[0]
        demand_fill_table.rename(columns={"%_met": "%_met_"+run_name}, inplace=True)
        df_merged=demand_fill_table
    else:
        last_name, df_merged = reduce(merge_fill, fill_list)
    #there were an odd number of runs so this last column didn't get renamed
    if '%_met' in df_merged.columns:
        df_merged=df_merged.rename(columns={'%_met': '%_met_'+last_run_name})
    df_merged["%met_increase"]=df_merged["%_met_"+last_run_name]-df_merged["%_met_"+first_run_name]
    y_lim_max=max(map(lambda grid: grid.axes[0].get_ylim()[1], grid_list))
    x_lim_max=max(map(lambda grid: grid.axes[0].get_xlim()[1], grid_list))
    delta=0
    for grid_num in range(len(grid_list)):
        grid=grid_list[grid_num]
        grid.set(ylim=(0, y_lim_max))
        grid.set(xlim=(0, x_lim_max))
        grid.savefig(image_list[grid_num+delta])
        #there was also a red, green chart added to image_list
        delta=delta+1
    results_pdf(df_merged, image_list, out_path)

def add_data_tags(df, trend_path):
    options=trend_path.split('_')
    df['Cut Level'] = options[3]
    df['Option'] = options[5]
    df['Target']=options[1]
    return df
    
def make_trends(trend_path, t_start, t_end):
    """Given a path to demand trends, filter for the war period and compute filled and unfilled for the results."""
    #ended here to load up the dataframe.
    df=load_trends(trend_path)
    df=df[(df['t']>=t_start) & (df['t']<=t_end)]
    df=df.groupby(['SRC', 'DemandGroup']).sum()
    df=df.reset_index()
    df=df[['SRC', 'DemandGroup', 'TotalRequired', 'Deployed']]
    df=df.rename(columns={'DemandGroup' : 'Demand', 
                          'TotalRequired' : 'Required',
                          'Deployed' : 'Filled'})
    df['Unfilled'] = df['Required'] - df['Filled']
    return df
    
def prep_data(path, t_start, t_end):
    trend_files = [ f.path for f in os.scandir(path) if not f.is_dir() and f.name.endswith('_trends.txt') and f.name != 'base_trends.txt']
    dfs = [add_data_tags(make_trends(f, t_start, t_end), f) for f in trend_files]
    res=pd.concat(dfs, axis=0, ignore_index=True)
    return res
    
def prep_for_rg_charts(path, t_start, t_end):
    """Given the path to a directory containing multiple demand trend files that each end with _trends.txt, """
    options = prep_data(path, t_start, t_end)

    ##add hifes (hife.xlsx exists there)
    hife_path = path+'HIFEs.xlsx'
    hifes=pd.read_excel(hife_path)
    options=pd.merge(left=options, right=hifes, how="left", on='SRC')
    options['HIFE'] = ~(options['Unit'].isnull())*1  
    ##add branch (branch.xlsx exists at path)
    branch_path = path+'Branch.xlsx'
    branches=pd.read_excel(branch_path)
    options=pd.merge(left=options, right=branches, how="left", on='SRC')
    options['Branch'] = options['Branch'].fillna('no_branch')
    ##spit base data
    ##instead of to csv, group_by Cut Level and Target 
    ##dataframe to csv without index
    ##then output 3 charts for each
    options.to_csv(path+"all_options.txt", index = False)
    
def add_periods(DemandTrends, m4_wkbk_path):
    periods=pd.read_excel(m4_wkbk_path, sheet_name = "PeriodRecords")
    bins=list(periods['FromDay'].map(lambda x: x-1))
    bins.append(sys.maxsize)
    labels=periods['Name']
    DemandTrends['periods']=pd.cut(x=DemandTrends['t'], bins=bins, labels=labels)                          


    