#!/usr/bin/env python
# coding: utf-8

#Load the data.
# libraries
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image

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
    g = g.fig.suptitle('Fill by Demand Type')

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
    sand_trends_by_demand_group(DemandTrends)
    plt.savefig(plot_path)
    # Show the graph
    plt.show()
    fills=fills_by_demand_group(DemandTrends)
    print(fills)
    return fills

def images_to_pdf(image_paths, filename):
    image_paths = [Image.open(x) for x in image_paths]
    im1=image_paths[0]
    im_list = image_paths[1:]
    im1.save(filename, "PDF" ,resolution=100.0, save_all=True,          append_images=im_list)
    
def dataframe_to_image(df, out_path):
    fig, ax =plt.subplots(figsize=(12,4))
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=df.values,colLabels=df.columns,loc='center')
    fig.savefig(out_path)