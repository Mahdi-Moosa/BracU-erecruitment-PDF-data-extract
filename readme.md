# Objective

This script generates a summary of applicant/candidate details from Brac University erecruitment PDF CVs (if you don't know what these files are, don't waste your time going through this repo)! 

The python script parses PDF files and recordes:
* Candidate's name
* Candidate's application serial number
* Candidate's obtained GPA/CGPA for undegraduate degree
* Candidate's obtained GPA/CGPA for postgraduate degree (CGPAs/GPAs of multiple institutes should be averaged - this functionality is implemented but not tested)
* Candidate's undergraduate and postgraduate degree granting institues (names are combined into the same string)
* Candidate's number of international publications
* Candidate's number of national publications

The script asks for a directory name. Once provided, the python script will parse all PDF files in the directory and will save aforementioned information for each of the candidates as a separate row. Output will be saved as a CSV file named `applicant_data.csv`.