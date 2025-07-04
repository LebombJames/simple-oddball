library(data.table)
library(tidyverse)
library(ggplot2)
library(viridis)

df <- fread("./out.csv")

n_epochs <- df |>
    group_by(time) |>
    count()
n_epochs <- n_epochs$n[[1]]

plot <- df |>
    group_by(time) |>
    summarise(
        TP9_Mean = mean(TP9),
        TP10_Mean = mean(TP10),
        AF7_Mean = mean(AF7),
        AF8_Mean = mean(AF8),
    ) |>
    pivot_longer(cols = -time, names_to = "variable", values_to = "value") |>
    ggplot(aes(x = time, y = value, colour = variable)) +
    geom_line() +
    geom_vline(xintercept = 0, colour = "red", alpha = 0.5) +
    scale_x_continuous(breaks = seq(from = -0.5, to = 1.5, by = 0.1)) +
    scale_colour_viridis_d(begin = 0.1, end = 0.8, option = "turbo", aesthetics = "colour", direction = -1) +
    theme_minimal() +
    theme(
        axis.title.y = element_blank()
    ) +
    labs(
        x = "Time",
        y = "Value",
        colour = "Channel",
        title = paste0(n_epochs, " epochs")
    )

ggsave(plot = plot, filename = "out.png", width = 10, height = 5, bg = "white")
