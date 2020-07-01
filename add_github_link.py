import pandas as pd

df = pd.read_csv("new-labeled-data-hh.csv")
repos = pd.read_csv("repositories.csv").set_index("name")

df["link"] = ""
for index, row in df.iterrows():
    url_base = repos.loc[row["repository"], "url"]
    url = "{}/commit/{}".format(url_base, row["hash"])
    df.loc[index, "link"] = url

df.to_csv("commits.csv", index=False, columns=["company","repository","link","hash","subject","message","changed_file","label"])