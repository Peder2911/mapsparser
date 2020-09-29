
import string
import pandas as pd

def daneCode(v):
    try:
        return "{0:05d}".format(int(v))
    except ValueError:
        return pd.NA

def ascii_to_int(v):
    try:
        return string.ascii_letters.index(char)
    except:
        return v 

def missing(data):
    def replace(v):
        try:
            if v > -1:
                return v
            else:
                return pd.NA
        except:
            return v

    for c in data.columns:
        data[c] = data[c].apply(replace)

    return data

def simplify(df):
    def fn(series):
        try:
            series = series.astype(pd.Int64Dtype())
        except:
            pass
        return series
    return df.apply(fn,0)
