from dwd.read_dwd import read_dwd
import pandas as pd
import datetime

pd.options.plotting.backend = "plotly"

A = 3.1935978
B = -37.4142478
C = 6.1824021
D = 0.0721566
v = 40.0


def mean_tmp(station):
    dwd_df = read_dwd(station)
    tmp = dwd_df.loc[:, " TMK"]
    tmp.name = "temp"
    return tmp


def norm_slp(temp_series):
    geom_temp_series = (
        temp_series
        + temp_series.shift(1) / 2
        + temp_series.shift(2) / 4
        + temp_series.shift(3) / 8
    ) / (1 + 0.5 + 0.25 + 0.125)
    slp_series = A / (1 + B / (geom_temp_series - v)) ** C + D
    slp_series.name = "norm_slp"
    return slp_series


def calc_forecast(
    temp_series,
    ref_start_date,
    ref_end_date,
    current_date,
    ref_start_meas,
    ref_end_meas,
    current_meas,
):
    slp = norm_slp(temp_series)
    slp_df = pd.concat([temp_series, slp], axis=1)

    ref_consumption = ref_end_meas - ref_start_meas
    ref_norm_slp = slp_df.loc[ref_start_date:ref_end_date, "norm_slp"].sum()
    ref_kundenwert = ref_consumption / ref_norm_slp

    ref_end_date_shift = (
        datetime.datetime.strptime(ref_end_date, "%Y%m%d") + datetime.timedelta(days=1)
    ).strftime("%Y%m%d")

    current_consumption = current_meas - ref_end_meas
    current_norm_slp = slp_df.loc[ref_end_date_shift:current_date, "norm_slp"].sum()
    current_kundenwert = current_consumption / current_norm_slp

    current_relative_saving = current_kundenwert / ref_kundenwert

    print(f"current_kundenwert / ref_kundenwert: {current_relative_saving:.2}")

    consumption_df = slp_df[ref_start_date:current_date]
    consumption_df = consumption_df.rename(columns={"norm_slp": "consumption"})
    consumption_df.loc[ref_start_date:ref_end_date, "consumption"] = (
        consumption_df.loc[ref_start_date:ref_end_date, "consumption"] * ref_kundenwert
    )
    consumption_df.loc[ref_end_date_shift:current_date, "consumption"] = (
        consumption_df.loc[ref_end_date_shift:current_date, "consumption"]
        * current_kundenwert
    )

    fig = consumption_df.plot()
    fig.write_html("slp.html")
    fig.show()


if __name__ == "__main__":
    tmp = mean_tmp("01503")
    calc_forecast(tmp, "20211001", "20221001", "20221104", 100000, 120000, 121000)
