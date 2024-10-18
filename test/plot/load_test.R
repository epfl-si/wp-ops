# install and activate packages
packages <- c("dplyr", "forcats", "ggplot2")
for (package in packages) {
    if (!require(package, character.only = TRUE)) {
        install.packages(package)
    }
}
library(dplyr)
library(forcats)
library(ggplot2)

# transform log files into data frame
files <- c("simulation_10.log", "simulation_20.log", "simulation_30.log")
data <- data.frame()
for (file in files) {
    gatling <- read.csv(file, sep = "\t", header = FALSE, col.names = c("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"))
    request <- gatling %>%
        filter(V1 == "REQUEST") %>%
        transmute(type = V2, url = V3, starttime = V4, endtime = V5, status = V6) %>% mutate(responsetime = endtime - starttime, test = paste0(gsub("[^0-9]", "", file), " users"))
    data <- rbind(data, request)
}

# show data
View(data)

# plot response time
plot <- ggplot(data, aes(x=test, y=responsetime)) + 
  geom_violin(draw_quantiles = c(0.50, 0.95, 0.99)) +
  geom_jitter(aes(colour=status, shape=status))
plot
