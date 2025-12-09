import pandas as pd
import numpy as np

# reading tsv file
billionaires = pd.read_csv("Billionaires.tsv", sep="\t")

# replacing empty strings with NULL values (converted from nan when converting file into sql)
billionaires = billionaires.replace("", np.nan)

# dropping unnecessary collumns
billionaires.drop(columns=["age", "category", "organization", "selfMade", "status", "title", "date"], inplace=True)

# renaming certain columns to match planning (rest of renaming is done in SQL)
billionaires.rename(columns={
    "rank":"position",
    "finalWorth":"wealth",
    "personName":"full_name",
    "country":"country_of_residence",
    "countryOfCitizenship":"country_of_citizenship",
    "birthDate":"birth_date",
    "state":"residence_state",
    "residenceStateRegion":"residence_region"
}, inplace=True)

# creating SOURCES table (separating sources for each billionaire)
sources = pd.DataFrame(columns=["b_id", "source"])
for line in range(billionaires.shape[0]):
    ss = billionaires.iloc[line]["source"].split(sep=", ")
    for s in ss:
        sources.loc[len(sources)] = {"b_id" : line, "source" : s}

# removing sources column from original table
billionaires.drop("source", axis=1, inplace=True)

# converting tables to sql format
import sqlite3
conn = sqlite3.connect("billionaires.db")
billionaires.to_sql("BILLIONAIRES_RENAMED", conn, if_exists="replace", index=False)
sources.to_sql("SOURCES", conn, if_exists="replace", index=False)