library(tidyverse)

cut_fill <- read.csv("notional fill by option.csv", stringsAsFactors=FALSE)

base_unfilled <- read.csv("notional base supply unfilled.csv", stringsAsFactors=FALSE)

data <- cut_fill %>%
  inner_join(base_unfilled, by=c("SRC", "Demand")) %>%
  mutate(Filled=ifelse(Unfilled-Base.Unfilled>=0, Filled, 1-Base.Unfilled),
         Unfilled=ifelse(Unfilled-Base.Unfilled>=0, Unfilled-Base.Unfilled, 0))

process_data <- function(data) {
  data %>%
  mutate(Filled=Filled/Required, Unfilled=Unfilled/Required, Base.Unfilled=Base.Unfilled/Required) %>%
    pivot_longer(cols=c(Filled, Unfilled, Base.Unfilled), names_to="Type", values_to="Value") %>%
    mutate(Label=ifelse(Value>0.2, str_c(round(Value*100, digits=0), "%"), "")) %>%
    mutate(Demand=ordered(Demand, levels=c("Defend", "Defeat", "Deter", "Disrupt")),
           Type=ordered(Type, levels=c("Base.Unfilled", "Unfilled", "Filled"))) %>%
    filter(Value>0)
}
  
src_data <- data %>% 
  process_data

hife_data <- src_data %>%
  filter(HIFE==1)

branch_data <- data %>% 
  group_by(Option, Branch, Demand) %>%
  summarize(Required=sum(Required), Filled=sum(Filled), Unfilled=sum(Unfilled), Base.Unfilled=sum(Base.Unfilled)) %>%
  process_data

summary_data <- data %>%
  group_by(Option, Demand) %>%
  summarize(Required=sum(Required), Filled=sum(Filled), Unfilled=sum(Unfilled), Base.Unfilled=sum(Base.Unfilled)) %>%
  process_data

risk_chart <- function(data, x) {
ggplot(data, aes(x=Option, y=Value, label=Label, fill=Type, width=0.95)) +
  geom_bar(position="stack", stat="identity") +
  geom_text(color="white", position=position_stack(vjust=0.5)) +
  labs(title=str_c("Fill by ", x, ", Demand, and Cut Option"), x=x, y="") +
  facet_grid(get(x)~Demand, switch="y") +
  scale_fill_manual(values=c("#AA1111", "#D2222D", "#238823")) +
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
    scale_fill_manual(values=c("#AA1111", "#D2222D", "#238823")) +
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

risk_chart(src_data, "SRC")
risk_chart(hife_data, "SRC")
risk_chart(branch_data, "Branch")
summary_risk_chart(summary_data)
