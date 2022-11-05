import zipfile
import os
from pathlib import Path
import pandas as pd
import numpy as np

dir_path = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(dir_path)), "data")


def station_path(station):
    return os.path.join(DATA_PATH, "dwd", station)


def unzip_dwd(filename, station):
    Path(station_path(station)).mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(os.path.join(DATA_PATH, filename), "r") as zip_ref:
        zip_ref.extractall(station_path(station))


def read_dwd(station):
    lsdir = os.listdir(station_path(station))
    filenames = [f for f in lsdir if f.startswith("produkt_klima_tag")]
    df = pd.concat(
        [
            pd.read_csv(
                os.path.join(station_path(station), filename),
                sep=";",
                index_col="MESS_DATUM",
                parse_dates=True,
                infer_datetime_format=True,
            )
            for filename in filenames
        ],
        axis=0,
    )
    df = df.sort_index()
    df = df[~df.index.duplicated(keep='first')]
    df = df.replace(-999, np.nan)
    df.index.name = "date"
    return df


if __name__ == "__main__":
    # filename = "tageswerte_KL_01503_akt.zip"
    # unzip_dwd(filename, "01503")
    filename = "tageswerte_KL_01503_19470201_20211231_hist.zip"
    unzip_dwd(filename, "01503")
    # read_dwd("01503")
