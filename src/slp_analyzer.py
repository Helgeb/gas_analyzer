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


def calc_kundenwert(start_date, end_date, start_meas, end_meas, slp_df):
    cons = end_meas - start_meas
    norm_slp = slp_df.loc[start_date:end_date, "norm_slp"].sum()
    return cons / norm_slp


def shift_date(date, days):
    return (
        datetime.datetime.strptime(date, "%Y%m%d") + datetime.timedelta(days=days)
    ).strftime("%Y%m%d")


def create_temp_forecast_df(start_date, temp_series):
    ind = pd.date_range(start=start_date, end=shift_date(start_date, 365), freq="1d")
    avg_temp = [
        temp_series[
            (temp_series.index.month == d.month)
            & (temp_series.index.day == d.day)
            & (temp_series.index.year > 1999)
        ].mean()
        for d in ind
    ]
    return pd.DataFrame(index=ind, data={"temp": avg_temp})


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

    ref_kundenwert = calc_kundenwert(
        ref_start_date, ref_end_date, ref_start_meas, ref_end_meas, slp_df
    )

    ref_end_date_shift = shift_date(ref_end_date, 1)

    current_kundenwert = calc_kundenwert(
        ref_end_date_shift, current_date, ref_end_meas, current_meas, slp_df
    )

    current_relative_saving = current_kundenwert / ref_kundenwert

    print(f"current_kundenwert / ref_kundenwert: {current_relative_saving:.2}")

    consumption_df = slp_df[ref_start_date:current_date]
    consumption_df = consumption_df.rename(columns={"norm_slp": "consumption"})
    consumption_df["kundenwert"] = ref_kundenwert
    consumption_df.loc[ref_start_date:ref_end_date, "consumption"]

    consumption_df.loc[ref_end_date:current_date, "kundenwert"] = current_kundenwert

    consumption_df.loc[:, "consumption"] = (
        consumption_df.loc[:, "consumption"] * consumption_df.loc[:, "kundenwert"]
    )

    forecast_df = create_temp_forecast_df(current_date, temp_series)
    forecast_slp = norm_slp(forecast_df["temp"])
    forecast_df = pd.concat([forecast_df, forecast_slp], axis=1)
    forecast_df["forecast_cons_ref_kundenwert"] = (
        forecast_df.loc[:, "norm_slp"] * ref_kundenwert
    )
    forecast_df["forecast_cons_current_kundenwert"] = (
        forecast_df.loc[:, "norm_slp"] * current_kundenwert
    )
    forecast_df = forecast_df.drop(columns=["norm_slp"])
    consumption_df = consumption_df.drop(columns=["kundenwert"])

    df = pd.concat([consumption_df, forecast_df], axis=0)

    fig = df.plot()
    fig.write_html("slp.html")
    fig.show()


if __name__ == "__main__":
    tmp = mean_tmp("01503")
    calc_forecast(tmp, "20211001", "20221001", "20221104", 100000, 120000, 121500)
