library(plyr)
library(tidyverse)
library(xlsx)

#global isTables to indicate that we are processing the static ResultsTable file instead of MARATHON output
isTables<-FALSE
#global level to indicate that we are creating bar charts with one row for each Cut Level
level<-FALSE

make_input_data <- function(option_path, out_name, base_path) {
  if(is.data.frame(option_path)){
    cut_fill=option_path
    base_path=select(base_path, c("SRC", "Demand", "Unfilled"))
    base_unfilled=rename(base_path, Base.Unfilled=Unfilled)
    cut_fill$Option=as.numeric(cut_fill$Option)
  } else {
    o_path=paste(options_path, out_name, '_input.csv', sep="")
    cut_fill <- read.csv(o_path, stringsAsFactors=FALSE)
    base_unfilled <- read.csv(base_path, stringsAsFactors=FALSE)
  }
  data <- cut_fill %>%
    inner_join(base_unfilled, by=c("SRC", "Demand"))
}

process_data <- function(data, demand_order) {
  if(isTables) {
    demand_order=order_of_demands
  }
  else if(missing(demand_order)){
    demand_order=sort(unique(data$Demand))
  }
  data <- data %>%
    mutate(Filled=Filled/Required, Unfilled=Unfilled/Required, Base.Unfilled=Base.Unfilled/Required) %>%
    #this  needs to go in process days
    #Make sure that the unfilled is not greater than the base unfilled.  If it is, we don't want to create a bar for the additional unfilled above the base.
    mutate(Filled=ifelse(Unfilled-Base.Unfilled>=0, Filled, 1-Base.Unfilled), 
           Unfilled=ifelse(Unfilled-Base.Unfilled>=0, Unfilled-Base.Unfilled, 0))
    if(level){
      #only one color for the bar now
      data<-mutate(data, Unfilled=Base.Unfilled+Unfilled, Base.Unfilled=Base.Unfilled-Base.Unfilled)
    }
  data <- data %>%
    pivot_longer(cols=c(Filled, Unfilled, Base.Unfilled), names_to="Type", values_to="Value") %>%
    mutate(Label=ifelse(Value>0.2, str_c(round(Value*100, digits=0), "%"), "")) %>%
    mutate(Demand=ordered(Demand, levels=demand_order),
           Type=ordered(Type, levels=c("Base.Unfilled", "Unfilled", "Filled")))
  if(level) {
    data=mutate(data, Cut.Level=ordered(Cut.Level, levels=level_order))
  }
  data %>%
    filter(Value>0)
}

summarize_data <- function(grouped_data){
  data <- summarize(grouped_data, Required=sum(Required), Filled=sum(Filled), Unfilled=sum(Unfilled), Base.Unfilled=sum(Base.Unfilled)) %>%
    process_data
}

risk_chart <- function(data, x) {
  plt=ggplot(data, aes(x=Option, y=Value, label=Label, fill=Type)) +
    geom_bar(position="stack", stat="identity", width=1, colour="black")
  if(x!="Branch") {
    plt=plt+geom_text(color="white", position=position_stack(vjust=0.5))
  }
  plt<-plt +
    labs(title=str_c("Fill by ", x, ", Demand, and Cut Option"), x=x, y="") +
    facet_grid(get(x)~Demand, switch="y")
  
  if(level){
    bar_colors<-summary_colors
  }
  else{
    bar_colors<-all_colors
  }
  plt+
    scale_fill_manual(values=bar_colors)+
    scale_x_reverse() +
    coord_flip() +
    theme_bw() +
    theme(axis.text.x=element_blank(),
          axis.ticks.x=element_blank(),
          axis.text.y=element_blank(),
          axis.ticks.y=element_blank(),
          legend.position="none",
          panel.spacing=unit(0, "lines"),
          plot.title=element_text(hjust=0.5),
          strip.text.y.left=element_text(angle=0))
    
}

summary_risk_chart <- function(data) {
  ggplot(data, aes(x=Option, y=Value, label=Label, fill=Type, width=0.95)) +
    geom_bar(position="stack", stat="identity") +
    geom_text(color="white", position=position_stack(vjust=0.5)) +
    labs(title="Fill by Cut Option and Demand", x="Cut Option", y="") +
    facet_wrap(~Demand, nrow=1) +
    scale_fill_manual(values=all_colors) +
    scale_x_reverse() +
    coord_flip() +
    theme_bw() + 
    theme(axis.text.x=element_blank(),
          axis.ticks.x=element_blank(),
          legend.position="none",
          panel.spacing=unit(0, "lines"),
          plot.title=element_text(hjust=0.5),
          strip.text.y.left=element_text(angle=0))
}

edit_hife_data <- function(src_data) {
  hifes=data.frame(read.xlsx(hifes_path, sheetName="Sheet1", stringsAsFactors=FALSE))
  hife_data<-filter(src_data, HIFE==1)
  hife_data$SRC <- factor(hife_data$SRC, levels=hifes$SRC)
  hife_data$SRC <- mapvalues(hife_data$SRC, from=hifes$SRC, to=hifes$Unit)
  return(hife_data)
}

save_charts <- function(options_path, out_name, path){
  data=make_input_data(options_path, out_name, path)
  if(isTables){
    options_path=dirname(in_path)
  }
  #likely too big to plot.
  src_data <- data %>%
    process_data
  #if there are no hifes, this will simply error out.
  hife_data <- edit_hife_data(src_data)
  
  plt=risk_chart(hife_data, "SRC")
  print(plt)
  ggsave(paste(out_name, "_hifes.jpeg", sep=""), plot=plt, device='jpeg', path=options_path)
  
  branch_data <-  summarize_data(group_by(data, Option, Branch, Demand)) 
  plt=risk_chart(branch_data, "Branch")
  print(plt)
  ggsave(paste(out_name, "_branch.jpeg", sep=""), plot=plt, device='jpeg', path=options_path)
  
  summary_data <- summarize_data(group_by(data, Option, Demand))
  plt=summary_risk_chart(summary_data)
  print(plt)
  ggsave(paste(out_name, "_summary.jpeg", sep=""), plot=plt, device='jpeg', path=options_path)
}

#args will be option file path and base file path'
#files are stuck in option file path + SRC, HIFE, Branch, Summary

#save_charts(paste(getwd(), "/", sep=""), 'notional_fill_by_option', paste(getwd(), '/notional_base_supply_unfilled_input.csv', sep=""))

args = commandArgs(trailingOnly=TRUE)
options_path=args[1]
out_name=args[2]
base_path=args[3]
if(!is.na(options_path)) {
  save_charts(options_path, out_name, base_path)
}

charts_for_levels <- function(df, group, base, scenario) {
  #used in process_data for the demand order as well as in save_charts
  isTables<<-TRUE
  save_charts(df, paste(c(group, scenario), collapse='_'), base)
  isTables<<-FALSE
}

save_level_chart <- function(chart_data, base_data, group) {
  data=make_input_data(chart_data, "", base_data) %>%
    filter(Option==base_option)
  isTables<<-TRUE
  level<<-TRUE
  level_data <- summarize_data(group_by(data, Option, Cut.Level, Demand))
  isTables<<-FALSE
  plt = risk_chart(level_data, "Cut.Level")
  level <<- FALSE
  print(plt)
  options_path=dirname(in_path)
  #group is vector so we need to collapse here.
  ggsave(paste(c(group, 'end-strength.jpeg'), collapse='_'), plot=plt, device='jpeg', path=options_path)
}

charts_for_scenarios <- function(df, group) {
  splits <- df %>%
    mutate(isBase=ifelse(Cut.Level==base_case, TRUE, FALSE)) %>%
    split(.$isBase)
  base_table<-splits$'TRUE'
  non_base_table<-splits$'FALSE'
  #save level charts here
  #now we want to show a row for 494, too
  level<<-TRUE
  save_level_chart(df, base_table, group)
  level<<-FALSE
  non_base_table %>%
    group_by(Cut.Level) %>%
    group_walk(partial(charts_for_levels, base=base_table, scenario=group))
}

static_charts <- function(static_path) {
  data.frame(read.xlsx(static_path, sheetName="Sheet1", stringsAsFactors=FALSE)) %>%
    #filter for Max only for now
    filter(Scenario=='Max') %>%
    group_by(Scenario) %>%
    group_walk(charts_for_scenarios)
}

summary_colors<-c("#D2222D", "#238823")
all_colors<-c("#1A1818", summary_colors)
#suck in results table
in_path=paste(getwd(), "/", "Results_Table.xlsx", sep="")
hifes_path=paste(getwd(), "/", "HIFEs.xlsx", sep="")
base_case=494
#use for save_level_charts
base_option=1
#the order of level chart output
level_order=c(494, 300)
#order of the columns named by the DemandGroup
order_of_demands=c("Moke", "Hinny")
static_charts(in_path)

