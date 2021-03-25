
from typing import List,Dict,Union
from collections import defaultdict
import json

import pandas as pd
import geopandas as gpd
import yaml

from util import simplify,missing,ascii_to_int

KEEP = {
        "p2_cod",
        "p2_muni",
        "pdet_name",
        "pdet",
    }

def getmetadata(dataframe: pd.DataFrame):
    dataframe = removeMissingRows(dataframe)
    return (fn(dataframe) for fn in (parseCodebook,parseDescriptions))

def parseCodebook(raw: pd.DataFrame)-> Dict[str,Dict[str,str]]:
    dat: Dict[str,Union[Dict,None]] = dict()
    nones = defaultdict(list) 

    replacements = {
        "Apply": "Yes",
        "Does not apply": "No"
    }

    def replace(value):
        try:
            return replacements[value]
        except KeyError:
            return value

    for _,r in raw.iterrows():
        vname = r["Variablename"].lower()

        try:
            v = yaml.safe_load(r["Alternatives"])
            v = {ascii_to_int(k):replace(v) for k,v in v.items()}
        except: 
            dat[vname] = None
            continue

        try:
            if any([x is None for x in v.values()]):
                nones[json.dumps(v,indent=4)].append(vname)
                dat[vname] = None
                continue

        except AttributeError:
            dat[vname] = None
            continue
            
        dat[vname] = v

    def fixyn(value):
        """
        Yaml parses Y/N as True/False.
        """
        if value is True:
            return "Yes"
        elif value is False:
            return "No"
        else:
            return str(value)

    try:
        comp = {k:v for k,v in dat.items() if v is not None}
        comp = {ko:{str(k):fixyn(v) for k,v in vo.items()} for ko,vo, in comp.items()}
    except:
        pass
    return comp

def parseDescriptions(dat: pd.DataFrame):
    """
    Makes a dictionary of variable descriptions used to annotate plots
    """
    dat.columns = [c.strip() for c in dat.columns]

    d = dict()
    for _,r in dat.iterrows():
        d.update({r["Variablename"].lower():r["Label"]})
    return d

def removeMissingRows(data:pd.DataFrame)->pd.DataFrame:
    """
    Removes rows that don't have a variable name.
    """
    return data[~data["Variablename"].isna()]

def fixYesNo(data,codebook):
    ynvars = []
    for varname,mappings in codebook.items():
        if "Yes" in mappings.values():
            try:
                rev = {v:k for k,v in mappings.items()}
                assert mappings["1"] == "Yes" 
                data[varname][data[varname] == int(rev["No"])] = 2
                del(mappings[rev["No"]])
                mappings["2"] = "No"
            except KeyError:
                pass
            else:
                ynvars.append(varname)
    return data,codebook

def packGeodata(data):
    data["geostring"] = data.geometry.apply(str)
    return data

if __name__ == "__main__":
    data = pd.read_csv("raw/maps.csv",encoding="latin1")
    cb,dsc = getmetadata(pd.read_excel("raw/codebook_labelled.xlsx"))

    data = simplify(data)
    data.columns = [cl.lower() for cl in data.columns]
    data = missing(data)

    data,cb = fixYesNo(data,cb)

    variables = set(cb.keys()).union(KEEP)
    variables = variables.intersection(set(data.columns))
    data = data[variables]

    geodata = gpd.read_file("raw/pdet.geojson")
    geodata.columns = [cl.lower() for cl in geodata]
    geodata = packGeodata(geodata)
    geodata = geodata[["pdetname","codane2","pdet","departamen","municipio","geostring"]]
    geodata.to_csv("out/pdet.csv",index=False)

    with open("out/codebook.json","w") as f:
        json.dump(cb,f)
    with open("out/descriptions.json","w") as f:
        json.dump(dsc,f)
    data.to_csv("out/maps.csv",index=False)
