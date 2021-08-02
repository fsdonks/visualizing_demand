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


    