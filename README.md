# ACM-DL-Front-Matter-Template

The template is optimized to be used for conferences that use [PCS](https://new.precisionconference.com/), the ACM E-Rights tool, and SIGCHI's QOALA tool.

## 1. Export Data to Generate Front Matter
* PCS Export: Export reviewer and committee member from PCS into `data-PCS`. Direct links to get the two files: https://new.precisionconference.com/XXX/chair/csv/committee and https://new.precisionconference.com/XXX/chair/csv/reviewers Note: This can only be done with the chair permission.
* E-Rights Export: To get the CSV, navigate to https://cms.acm.org/cms_proceeding_papers_public.cfm?proceedingID=YOURPROCEEDINGSID&confID=YOURCONFERENCEID, at the top left press the `Create CSV` button and copy-and-pasted the content from the new window into the `export.csv` in the `data-erights` folder.
* QOALA Export: One option to group the papers in sessions in the ACM DL is to use the QOALA scheduling data directly. Export the session data from QOALA as `.json` file and save it as `export.json` in the `data-QOALA` folder. TPCs typically have access to QOALA to export the file.

## 2. Adjust Generation Settings
After exporting all data, adjust the `proceedingsInfo.csv` file in `data` folderto reflect all venues the conference has accordingly. Each venue (e.g., full papers) is reflected by one row in the file. Columns:
* Name -- The name of the venue, e.g., Full Paper
* VenueId -- Prefix code for the running number of the entries in the Table of Contents. For instance, "ws" turns to "WS001," etc.
* PCSId -- code of the venue in PCS, e.g., XXX when the link is https://new.precisionconference.com/XXX/
* NameCommittee -- Name of the committee, e.g., Associated Chairs, Jury Member
* NameReviewers -- Name of the reviewer, e.g., Reviewers, Jury Member
* Prefix -- Prefix set in PCS in the "General settings" of each venue
* Order -- Order of the venue in the Table of Content latex export
* UseQOALASessions -- True if the sessions from QOALA should be used. False otherwise.

## 3. Generate Files
Exceute the `generateFrontMatter.ipynb` script using `jupyter nbconvert --execute --to notebook --inplace generateFrontMatter.ipynb` or start a jupter server to jun the script. 

## 4. Create Extra PDF Files
* Title Page (`cover/cover_font.pdf`): This can be designed to match the conference theme. The conference name, general chair names, and technical program chair names should be included. The original layout is from [ACM Styleguide](http://identitystandards.acm.org/styleguide/).
* Last Page (`cover/cover_back.pdf`): This can be designed to match the conference theme. The recommendation is to include the sponsors.
* Copyright Page (`acm-copyright.pdf`): Fill in the [ACM Copyright template](https://www.acm.org/binaries/content/assets/publications/gi-verso.doc) to create the `acm-copyright.pdf` (see the [ACM General Instructions for Proceedings Volumes] (https://www.acm.org/publications/gi-proceedings-current) for all details). This page must appear as the second page in the final font matter.
