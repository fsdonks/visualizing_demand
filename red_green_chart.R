library(tidyverse)
library(magrittr)
library(dplyr)

red.green.chart.data <- function(original.data, original.data.order) {
  original.data %>%
    pivot_longer(!SRC, names_to="Demand", values_to="Filled") %>%
    mutate(Unfilled=ifelse(Filled>=0, 1-Filled, -1)) %>%
    pivot_longer(cols=3:4, names_to="Type", values_to="Value") %>%
    mutate(Demand=ordered(Demand, levels=original.data.order),
           Type=ordered(Type, levels=c("Unfilled", "Filled"))) %>%
    filter(Value>0)
}

red.green.chart.plot <- function(original.data, original.data.order) {
  if(missing(original.data.order)){
    original.data.order=sort(names(original.data)[c(-1)])
  }
  print(names(original.data))
  in.data=red.green.chart.data(original.data, original.data.order)
  return(ggplot(in.data, aes(x=SRC, y=Value, fill=Type, width=0.95)) +
    geom_bar(position="stack", stat="identity") +
    labs(title="", x="", y="") +
    facet_wrap(vars(Demand), nrow=1) +
    scale_fill_manual(values=c("#D2222D", "#238823")) +
    scale_x_discrete(limits=rev) +
    coord_flip() +
    theme_bw() + 
    theme(axis.text.x=element_blank(),
          axis.ticks.x=element_blank(),
          legend.position="none",
          panel.spacing=unit(0, "lines")))
}

demand.trends.to.plot.data <- function(path) {
  df <- read.table(path, sep='\t', header=TRUE) %>%
    group_by(SRC, DemandGroup) %>%
    summarise(fill=sum(Deployed)/sum(TotalRequired)) %>%
    pivot_wider(names_from=DemandGroup, values_from=fill)
}

#red.green.chart.plot(read.csv("data.csv", stringsAsFactors=FALSE),
#                     c("Defend", "Defeat", "Deter", "Disrupt"))

#red.green.chart.plot(demand.trends.to.plot.data("demand_trends.txt"))

args = commandArgs(trailingOnly=TRUE)
in.file.path=args[1]
out.file.name=args[2]
out.file.path=args[3]
if(!is.na(in.file.path)) {
plt=red.green.chart.plot(demand.trends.to.plot.data(in.file.path))
ggsave(out.file.name, plot=plt, device='jpeg', path=out.file.path)
}
