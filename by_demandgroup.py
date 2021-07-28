#!/usr/bin/env python
# coding: utf-8

#Load the data.
# libraries
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

def trends_by_demand_type(DemandTrends):
    DemandTrends['TotalFilled']=DemandTrends['TotalFilled']
    DemandTrends["Unmet"]=DemandTrends["TotalRequired"] - DemandTrends["Deployed"]
    DemandTrends["Unmet"]=DemandTrends["Unmet"]+DemandTrends["TotalFilled"]
    #here, group by interest, then send through:
    return DemandTrends.groupby(['t', 'DemandGroup']).sum().reset_index()


# In[5]:


#Need to do this for a stacked, step-style stacked area chart.
#Facet grid is nice because it makes vertical axis consistent.

def sand_trends_by_demand_group(DemandTrends):
    # Create a grid : initialize it
    g = sns.FacetGrid(trends_by_demand_type(DemandTrends), col='DemandGroup', hue='DemandGroup', col_wrap=4, )
    
    # Add the line over the area with the plot function
    g = g.map(plt.plot, 't', 'TotalFilled', drawstyle="steps", color='green')
    g = g.map(plt.plot, 't', 'Unmet', drawstyle="steps", color='black')
    # Fill the area with fill_between
    g = g.map(plt.fill_between, 't', 'TotalFilled', step='pre', color='green').set_titles("{col_name} DemandGroup")
    g = g.map(plt.fill_between, 't', 'Unmet', 'TotalFilled', step='pre', color='black').set_titles("{col_name} DemandGroup")
    
    # Control the title of each facet
    g = g.set_titles("{col_name}")
     
    # Add a title for the whole plot
    plt.subplots_adjust(top=0.92)
    g = g.fig.suptitle('Evolution of the value of stuff in 16 countries')

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

def process_trends(demand_trends_path):
    # Create a dataset
    df = pd.read_csv(demand_trends_path, sep="\t")
    sand_trends_by_demand_group(df)
    # Show the graph
    plt.show()
    print(fills_by_demand_group(df))