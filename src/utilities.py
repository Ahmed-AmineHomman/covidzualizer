import matplotlib.pyplot as plt


def process(data, countries, variables):
    data["country"] = data["country"].str.lower()
    data = (data
            .loc[data["country"].isin(countries)]
            .groupby(by=["date", "country"])
            .agg({var: "sum" for var in variables})
            .unstack(level=1)
            .resample(rule="D")
            .sum()
            .rolling(window=7, center=False)
            .mean()
            .iloc[6:, :]
            .fillna(0)
            .astype(int)
            .sort_index()
            .stack(level=1))
    data.columns.name = "variable"
    return (data
            .stack()
            .rename("score")
            .reset_index())


def plot(data, countries, variables):
    fig = plt.figure(figsize=(12, 8))
    axes = list()
    plot_count = len(variables)
    idx = 1
    for variable in variables:
        axes.append(fig.add_subplot(plot_count, 1, idx))
        for country in countries:
            (data
             .loc[data["country"] == country]
             .loc[data["variable"] == variable]
             .set_index("date")["score"]
             .plot(style="-", ax=axes[-1]))
        axes[-1].set_ylabel(variable)
        axes[-1].grid(True)
        axes[-1].legend(countries)
        idx += 1
    axes[-1].set_xlabel("date")
    fig.tight_layout()
    return fig, axes
