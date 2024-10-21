# install and activate packages
packages <- c("dplyr", "forcats", "ggplot2", "jsonlite")
for (package in packages) {
  if (!require(package, character.only = TRUE)) {
    install.packages(package)
  }
}
library(dplyr)
library(forcats)
library(ggplot2)

# transform log files into data frame
files <- c("mplp_2024-10-18_1729263520.out.json")
data <- fromJSON(files) 

# show data
View(data)

# plot response time
plot <- ggplot(data, aes(x="", y=wait_time)) + 
  geom_jitter() +
  geom_violin(draw_quantiles = c(0.50, 0.95, 0.99)) +
  ggtitle("Plot of the time it takes for a site to return to normal after the MariaDB Pod has been deleted") +
  xlab("sites") +
  ylab("Time (s)") 

plot
