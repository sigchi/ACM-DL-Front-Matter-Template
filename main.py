import os
import re
import sys
from pandas.api.types import CategoricalDtype
import numpy as np
import pandas as pd
import math
import csv
import json
from unidecode import unidecode
import os.path

# %% [markdown]
# # Read Proceedings Information
# Update the `proceedingsInfo.csv` file according to your conference and the filed downloaded from PCS.

dfCommittee = pd.read_csv("./data/committee.csv")
dfCommittee.head()

dfVenues = pd.read_csv("./data/proceedingsInfo.csv")
dfVenues = dfVenues.sort_values("Order")
dfVenues.head()

print("Generation settings read from data/proceedingsInfo.csv:\n")
print(dfVenues[[
    "Order", "Name", "VenueId", "PCSId",
    "NameCommittee", "NameReviewers", "Prefix", "UseQOALASessions", "ShowReviewCount",
]].to_string(index=False))
print()

answer = input("Proceed with generating the front matter using these settings? [y/N]: ").strip().lower()
if answer not in ("y", "yes"):
    print("Aborted. No files were generated.")
    sys.exit(0)

def hasValue(x):
    return isinstance(x, str) and x.strip() != ""

def checkDataFiles(dfVenues):
    print("Checking data files:")
    allRequiredPresent = True

    def report(path, label):
        nonlocal allRequiredPresent
        exists = os.path.isfile(path)
        status = "found  " if exists else "MISSING"
        print(f"  [{status}] {path} ({label})")
        if not exists:
            allRequiredPresent = False

    report("./data-erights/export.csv", "ACM E-Rights export")

    for i, e in dfVenues.iterrows():
        if hasValue(e.NameCommittee):
            report(f"./data-PCS/{e.PCSId}_committee.csv", f"{e.Name}: {e.NameCommittee}")
        if hasValue(e.NameReviewers):
            report(f"./data-PCS/{e.PCSId}_reviewers.csv", f"{e.Name}: {e.NameReviewers}")

    if dfVenues["UseQOALASessions"].any():
        report("./data-QOALA/export.json", "QOALA session data")

    print()

    if not allRequiredPresent:
        print("Aborted: a required data file is missing. Set the corresponding Name column in data/proceedingsInfo.csv to blank if this venue does not use it.")
        sys.exit(1)

checkDataFiles(dfVenues)

outputDirs = ["committee", "content", "export"]
for outDir in outputDirs:
    if not os.path.isdir(outDir):
        print(f"Creating missing output folder: {outDir}/")
        os.makedirs(outDir, exist_ok=True)

# %% [markdown]
# # Generate Committee Files

def getReviewCountSuffix(e, showReviewCount):
    if not showReviewCount:
        return ""
    completed = e["Reviews assigned"] - e["Reviews incomplete"]
    reviewWord = "review" if completed == 1 else "reviews"
    return f" ({completed} {reviewWord} completed)"

def getCommittee(PCSId, showReviewCount=False):
    path = f"./data-PCS/{PCSId}_committee.csv"
    if (not os.path.isfile(path)):
        print(f"{PCSId} has no committee file")
        return []

    df = pd.read_csv(path)
    df = df[(df["Reviews assigned"] - df["Reviews incomplete"]) > 0]

    if (len(df) == 0):
        print(f"{PCSId} has no reviewers")
        return []

    lstText = []
    df["Family name"] = df["Family name"].str.title()
    df["First name"] = df["First name"].str.title()
    #df["Middle name"] = df["Middle name"].str.title()
    df = df.sort_values(["Family name", "First name", "Middle initial"])

    for i, e in df.iterrows():
        for i in range (1,7):
            if isinstance(e[f"Affil {i} Institution"], str):
                break
        aff = ""
        if isinstance(e[f"Affil {i} Institution"], str):
            aff = f'{e[f"Affil {i} Institution"]}, {e[f"Affil {i} Country"]}'

        aff = aff.replace("&", "\\&")
        reviewCountSuffix = getReviewCountSuffix(e, showReviewCount)
        if isinstance(e["Middle initial"], str):
            lstText.append(f'{e["First name"]} {e["Middle initial"]} {e["Family name"]}, \\emph{{{aff}}}{reviewCountSuffix}\\\\')
        else:
            lstText.append(f'{e["First name"]} {e["Family name"]}, \\emph{{{aff}}}{reviewCountSuffix}\\\\')

    if (len(df) > 50):
        lstText.insert(0, "\\begin{multicols}{2}")
        lstText.append("\\end{multicols}")
    else:

        lstText.insert(0, "%\\begin{multicols}{2}")
        lstText.append("%\\end{multicols}")
    lstText.append("")
    return lstText

def getReviews(PCSId, showReviewCount=False):
    path = f"./data-PCS/{PCSId}_reviewers.csv"
    if (not os.path.isfile(path)):
        print(f"{PCSId} has no reviwer file")
        return []

    df = pd.read_csv(path)
    df = df[(df["Reviews assigned"] - df["Reviews incomplete"]) > 0]

    if (len(df) == 0):
        print(f"{PCSId} has no reviewers")
        return []

    # Ensure that all names start with a capital first latter.
    df["Family name"] = df["Family name"].apply(lambda x: x[0].title()+x[1:] if len(x)>2 else x)
    df["First name"] = df["First name"].apply(lambda x: x[0].title()+x[1:] if len(x)>2 else x)
    if "Middle name"in df.columns:
        df["Middle name"] = df["Middle name"].apply(lambda x: x[0].title()+x[1:] if len(x)>2 else x)

    df = df.sort_values(["Family name", "First name", "Middle initial"])
    lstText = []
    lstText.append("\\begin{multicols}{3}")
    for i, e in df.iterrows():
        reviewCountSuffix = getReviewCountSuffix(e, showReviewCount)
        if isinstance(e["Middle initial"], str):
            lstText.append(f'{e["First name"]} {e["Middle initial"]} {e["Family name"]}{reviewCountSuffix}\\\\')
        else:
            lstText.append(f'{e["First name"]} {e["Family name"]}{reviewCountSuffix}\\\\')
    lstText.append("\\end{multicols}")
    lstText.append("")
    return lstText

lastPosition = ""

lstExport = []
lstExport.append("% Please list all organization committee members and their respected roles below. The best source to fill in this document is the conference webpage.")

for i, e in dfCommittee.iterrows():

    if (lastPosition != e.Position):
        lastPosition = e.Position
        lstExport.append("")
        lstExport.append(f"\\subsection{{{e.Position}}}")

    lstExport.append(f'{e.Name}, \\emph{{{e.Affiliation}, {e.Country}}}\\\\')

if (len(lstExport) > 0):
        with open(f'committee/committee-organizer.tex', 'w', encoding="utf-8") as fp:
            fp.write('\n'.join(lstExport))

for i, e in dfVenues.iterrows():
    lstExport = []
    lstExport.append("% If this venue/track has subcommittees, you might want to split the \\subsection{Committee Member} into different \\subsubsections for the different committees.")
    lstExport.append("")
    dfX = dfCommittee[dfCommittee.VenueId == e.VenueId]

    if (len(dfX) > 0):
        lstExport.append(f"\\subsection{{{e.Name} Chairs}}")
        for j, c in dfX.iterrows():
            lstExport.append(f"{c.Name}, \\emph{{{c.Affiliation}, {c.Country}}}\\\\")
    else:
        print(f"WARNING: {e.Name} has no chairs assigned to it. use the VenueId '{e.VenueId}' and assign them in the ./data/committee.csv to the respective chair(s)")

    lstExport.append("")
    lstExport.append("")

    if hasValue(e.NameCommittee):
        commitee = getCommittee(e.PCSId, showReviewCount=e.ShowReviewCount)
        if (len(commitee) > 0):
            lstExport.append(f"\\subsection{{{e.NameCommittee}}}")
            lstExport.extend(commitee)

    if hasValue(e.NameReviewers):
        reviewers = getReviews(e.PCSId, showReviewCount=e.ShowReviewCount)
        if (len(reviewers) > 0):
            lstExport.append(f"\\subsection{{{e.NameReviewers}}}")
            lstExport.extend(reviewers)

    if (len(lstExport) > 0):
        with open(f'committee/committee-{e.VenueId}.tex', 'w', encoding="utf-8") as fp:
            fp.write('\n'.join(lstExport))

# %% [markdown]
# # Loading ACM E-Rights CSV File
# To get the CSV, navigate to https://cms.acm.org/cms_proceeding_papers_public.cfm?proceedingID=YOURPROCEEDINGSID&confID=YOURCONFERENCEID, at the top left press the `Create CSV` button and copy-and-pasted the content from the new window into the `export.csv` in the `data-erights` folder.

dfACM = pd.read_csv("./data-erights/export.csv")

## Old code to read the ACM export file;. The format was not a valid CSV.
# file1 = open("./data-erights/export.csv", 'r')
# lines = file1.readlines()
# lstLines = []
# for x in lines[1:]:
#     e = x[1:].split('","')

#     if ("WITHDRAWN" in x):
#         print("WITHDRAWN", x.split(",")[0].replace('"', ""))
#     elif ("DUPLICATE INSERTS" in x):
#         print("DUPLICATE INSERTS", x.split(",")[0].replace('"', ""))
#     else:
#         lstLines.append(e)


# columns = lines[0]
# columns = columns.replace('"', "").replace(' ', "").replace("\n", "").split(",")
# if "ACMNo." in columns:
#     print("Warning: It seems you are using a old e-rights export format. Please update the export format.")

# print(columns)
# dfACM = pd.DataFrame(lstLines)
# dfACM.columns = columns


dfACM = dfACM.rename(columns={"Contact No.": "ID", "ACM No.": "ACMNo"})

print("Processing data-erights/export.csv:")

dX = dfACM[dfACM["Rights Granted"].str.startswith("WITHDRAWN")]
if (len(dX) > 0):
    print(f'  - {len(dX)} paper(s) marked "WITHDRAWN" by ACM E-Rights, excluded from the proceedings: {dX["ID"].to_list()}')
dfACM = dfACM[~dfACM["Rights Granted"].str.startswith("WITHDRAWN")]

dX = dfACM[dfACM["Rights Granted"].str.startswith("DUPLICATE INSERTS")]
if (len(dX) > 0):
    print(f'  - {len(dX)} paper(s) marked "DUPLICATE INSERTS" by ACM E-Rights (the paper was submitted into the proceedings database more than once), excluded from the proceedings: {dX["ID"].to_list()}')
dfACM = dfACM[~dfACM["Rights Granted"].str.startswith("DUPLICATE INSERTS")]

dfACM['Email'] = dfACM.Email.apply(lambda x: x.split(" ")[0])
dfACM['Signed'] = dfACM['Non-ACM Copyright'].apply(lambda x: x[:-3]) != "load For"
dfACM.Title = dfACM.Title.apply(lambda x: x.split(" \\setcopyright{")[0])

dfACM["Prefix"] = dfACM.ID.apply(lambda x: re.sub(r'[0-9]', '', x))

dfACM["TitleRaw"] = dfACM.Title.str.replace('"', '')
dfACM["TitleRaw"] = dfACM.TitleRaw.str.replace('[', '', regex=False)

## Might needs to be applied to fix LaTex issues.
#dfACM["TitleRaw"] = dfACM.TitleRaw.str.replace('`', '', regex=False)
#dfACM["TitleRaw"] = dfACM.TitleRaw.str.replace('"', '', regex=False)
#dfACM["TitleRaw"] = dfACM.TitleRaw.str.replace("'", '', regex=False)
#dfACM["TitleRaw"] = dfACM.TitleRaw.str.replace('(', '', regex=False)
#dfACM["TitleRaw"] = dfACM.TitleRaw.str.replace('#', '', regex=False)
#dfACM["TitleRaw"] = dfACM.TitleRaw.str.lower()

# Remove duplicates, this is possible when the contact authors can not sign the copyright for all authors.
dX = dfACM[dfACM.duplicated("ID", keep="first")]
if (len(dX) > 0):
    print(f'  - {len(dX)} duplicate row(s) for paper ID(s) already seen (can happen when not all contact authors signed the copyright release), keeping the first occurrence: {dX["ID"].to_list()}')
dfACM = dfACM.drop_duplicates("ID")

print()

dfACM = dfACM[["ACMNo", "ID", "Prefix", "Title", "Author", "DOI"]]

dfACM.head()

df = pd.merge(dfACM, dfVenues[["Prefix", "Name", "VenueId"]], on="Prefix")

myOrder = CategoricalDtype(
    dfVenues.sort_values("Order").Prefix.to_list(),
    ordered=True
)

df.Prefix = df.Prefix.astype(myOrder)
df = df.sort_values(["Prefix", "Title"])

df.head()

# %% [markdown]
# # Load Session Data From QOALA
# QOALA is the SIGCHI tool to schedule conferences, see https://services.sigchi.org/qoala. Exort the session data from QOALA as `.json` file.

exportFileQOALA = "./data-QOALA/export.json"

if (os.path.isfile(exportFileQOALA)):
    print("Info: Using QOALA data for the sessions")
    with open(exportFileQOALA, 'r', encoding="utf-8") as f:
        qoala = json.load(f)

    if (qoala["schemeVersion"] != 7):
        print("WARNING: This script was not tested with the QOALA expert scheme version. It might not fully working.")

    dfQPapers = pd.DataFrame(qoala["contents"])

    if len(dfQPapers) > 0:

        dfX = dfQPapers[dfQPapers.sessionIds.apply(lambda x: len(x) > 1)]
        if len (dfX) > 0:
            print(f'WARNING: The following papers are in more than one session: {dfX.importedId.to_list()}')

        dfQPapers.sessionIds = dfQPapers.sessionIds.apply(lambda x: x[0])

        dfQSessions = pd.DataFrame(qoala["sessions"])
        dfQSessions = dfQSessions.rename(columns={"id":"sessionId", "name":"SessionName"})

        dfQoala = pd.merge(dfQPapers, dfQSessions[["sessionId", "SessionName"]], left_on="sessionIds", right_on="sessionId", how="left")[["importedId", "title", "SessionName"]]
        dfQoala["PCSId"] = dfQoala.importedId.apply(lambda x: x.split("-")[0])
        dfQoala["IdRaw"] = dfQoala.importedId.apply(lambda x: x.split("-")[1])

        myMap = dfVenues.set_index("PCSId")["Prefix"].to_dict()
        dfQoala["Prefix"] = dfQoala.PCSId.map(myMap)

        dfQoala["ID"] = dfQoala["Prefix"] + dfQoala["IdRaw"]
        dfQoala.head()
    else:
        print("WARNING: QOALA data for the papers is not available.")

else:
    for i, e in dfVenues.iterrows():
        df.loc[df.Prefix == e.Prefix, "SessionName"] = e.Name

    print("WARNING: QOALA data for the papers is not available.")

if 'dfQoala' in globals():
    if ("SessionName" in df.columns):
        del df["SessionName"]
    df = pd.merge(df, dfQoala[["ID", "SessionName"]], on="ID", how="outer")

    for i, e in dfVenues.iterrows():
        if (not e.UseQOALASessions):
            df.loc[df.Prefix == e.Prefix, "SessionName"] = e.Name

df.Prefix.value_counts().reset_index()

# %% [markdown]
# # Generate the TOC

lstExport = []
lstExport.append("%% This file lists all items that are in the proceedings in the ACM DL. This again varies depending on if you have a companion proceedings or not.")
lstExport.append("%% Note: For conferences that will publish the full papers in PACMHCI, then the full papers are not to be listed here.")
lstExport.append("")
lastPrefix = ""
counterTOC = 1

tapsTOC=[]
lstAuthorIndex = []
lstDetails = []
for j, f in dfVenues.sort_values("Order").iterrows():
    dfTrack = df[df.Prefix == f.Prefix]

    counter = 1
    lastSessionName = ""

    lstExport.append(f'\\subsection{{{f.Name}}}')

    if (f.UseQOALASessions):
        dfTrack = dfTrack.sort_values(["SessionName", "Title"])
    else:
        dfTrack = dfTrack.sort_values(["Title"])

    for i, e in dfTrack.iterrows():

        if (lastSessionName != e.SessionName) & (f.UseQOALASessions):
            lastSessionName = e.SessionName
            if (counter != 1):
                lstExport.pop()
                lstExport.append(f'\\end{{enumerate}}')
                lstExport.append("")
            lstExport.append(f'\\subsubsection{{{e.SessionName}}}')
            lstExport.append(f'\\begin{{enumerate}}')
        elif (counter == 1):
            lstExport.append(f'\\begin{{enumerate}}')

        lstExport.append(f'%PCS ID: {e.ID}')
        TOC_ID = f"{e.VenueId.upper()}{counter:03}"
        lstExport.append(f'\\item[\\href{{{e.DOI}}}{{\\textbf{{{TOC_ID}}}}}]')

        xx = f'\\href{{{e.DOI}}}{{\\textbf{{{e.Title}}}}}\\\\'
        lstExport.append(xx.replace("&", "\\&").replace("#", "\\#"))
        for x in e.Author.split(";"):
            x = x.split(":")

            if (len(x) > 1):
                xx = f"{x[0]}, \\emph{{{x[1]}}}\\\\"
            else:
                xx = f"{x[0]}\\\\"

            lstAuthorIndex.append([x[0], TOC_ID])
            lstExport.append(xx.replace("&", "\\&").replace("#", "\\#").replace(",", ", ").replace("  ", " "))

        xx = f'\\textbf{{DOI:}} \\href{{{e.DOI}}}{{{e.DOI}}}\\\\'
        lstExport.append(xx.replace("&", "\\&").replace("#", "\\#"))
        lstExport.append("")

        counter = counter + 1
        counterTOC = counterTOC + 1

        lstDetails.append({"ID": e.ID, "TOC_ID":TOC_ID, "Order":counterTOC})

    lstExport.pop()
    lstExport.append(f'\\end{{enumerate}}')
    lstExport.append("")
    lstExport.append("")

if (len(lstExport) > 0):
    with open(f'./content/content.tex', 'w', encoding="utf-8") as fp:
        fp.write('\n'.join(lstExport))

# %% [markdown]
# # Generate the TOC for APTARA
# This puts the TOC entries into "sessions." Sessions are the structure ACM used in the ACM DL; for example, see the structure here on the left side: https://dl.acm.org/doi/proceedings/10.1145/3544548
# The list is to be sent via email to APTARA so they can sort them accordingly and prepare for the ACM upload.

dfAptaraExport = pd.merge(df, pd.DataFrame(lstDetails), on="ID")
dfAptaraExport = dfAptaraExport[["Order", "ACMNo", "ID", "TOC_ID", "Title", "SessionName", "DOI"]]
dfAptaraExport = dfAptaraExport.sort_values(["Order", "TOC_ID"])
dfAptaraExport.to_csv("./export/TOC-for-APTARA.csv", index=False)
dfAptaraExport
