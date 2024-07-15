import tabula
import pandas as pd
import PyPDF2
import re
import numpy as np
import os


def extract_tables_from_pdf(file_path):
    """Extracts tables from a PDF into a dictionary of DataFrames.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        dict: A dictionary where keys are table names ("table_1", "table_2", etc.) 
              and values are the corresponding DataFrames.
    """
    table_dfs = {}

    # Read all tables, handling potential table splits by merging them based on column names.
    all_tables = tabula.read_pdf(file_path, pages="all", multiple_tables=True, lattice=True)
    for table in all_tables:
        df = pd.DataFrame(table)
        if table_dfs and set(df.columns) == set(table_dfs["table_1"].columns):
            # If columns match the first table, assume it's a continuation and concatenate.
            table_dfs["table_1"] = pd.concat([table_dfs["table_1"], df])
        else:
            # Otherwise, add it as a new table.
            table_dfs[f"table_{len(table_dfs) + 1}"] = df

    return table_dfs


def extract_gpa(df, column_name):
    """Extracts and standardizes GPA values from a specified DataFrame column.

    Args:
        df (pd.DataFrame): The DataFrame containing the GPA data.
        column_name (str): The name of the column with GPA values.

    Returns:
        pd.DataFrame: The DataFrame with standardized GPA values in the specified column.
    """
    if column_name not in df.columns or df[column_name].dtype == 'float64':  # Early exit if not needed
        return df
    def _standardize_gpa(value):
        """Helper function to standardize GPA to a 4.0 scale."""
        if isinstance(value, float):
            return value  # Already a float, no need to process further
        match = re.search(r"(\d+\.?\d*)\s*(?:\n*\s*out\s+of\s*\n*|/)(\d+\.?\d*)", str(value), re.IGNORECASE)
        if match:
            gpa, scale = map(float, match.groups())
            return (gpa / scale) * 4 if scale != 4 else gpa
        return np.nan  # Not a recognized GPA format
    df = df.copy()  # Avoid modifying the original DataFrame
    df[column_name] = df[column_name].astype(str).apply(_standardize_gpa)
    return df


def extract_applicant_info(file_path):
    """Extracts applicant name and publication counts from a PDF."""
    with open(file_path, 'rb') as file:
        text = "".join(page.extract_text() for page in PyPDF2.PdfReader(file).pages)

    name = re.search(r"Name\s*:\s*(.*)", text).group(1) if re.search(r"Name\s*:\s*(.*)", text) else None

    def _extract_publication_count(pattern):
        match = re.search(pattern, text)
        return int(match.group(1)) if match else 0

    return {
        "Name": name,
        "Publications_National": _extract_publication_count(r"No\. of Publication National\s*:\s*(\d+)"),
        "Publications_International": _extract_publication_count(r"No\. of Publication International\s*:\s*(\d+)"),
        "Submission #": re.search(r"erecruitment-submission-(\d+)\.pdf", file_path).group(1)
        if re.search(r"erecruitment-submission-(\d+)\.pdf", file_path)
        else None,
    }


def get_grad_postgrad_data(tables_dict):
    """Calculates aggregated GPA and affiliation data for graduate and postgraduate levels."""
    # print(tables_dict['table_1'].keys)
    extracted_df = extract_gpa(tables_dict['table_1'], 'Result')
    grad_postgrad_df = extracted_df[
        extracted_df['Level'].isin(['Graduation', 'Postgraduation'])
    ][['Level', 'Name of\rInstitution', 'Result']]

    def _agg_func(series):
        if pd.api.types.is_numeric_dtype(series):
            return series.mean()
        elif pd.api.types.is_string_dtype(series):
            return ', '.join(series.dropna())
        return np.nan

    agg_data = grad_postgrad_df.groupby('Level').agg(_agg_func).T.loc['Result']

    return {
        "Graduation GPA": agg_data.get('Graduation', np.nan),
        "Postgraduation GPA": agg_data.get('Postgraduation', np.nan),
        "Affiliations": grad_postgrad_df.groupby('Level').agg(_agg_func).T.loc['Name of\rInstitution'].tolist(),
    }

# Main execution
def main():
    folder_path = input("Enter the path to the folder containing PDF files: ")

    all_results = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            print(f'Starting reading of file {file_path}')
            try:
                tables_dict = extract_tables_from_pdf(file_path)
                # print(tables_dict)
                applicant_info = extract_applicant_info(file_path)

                # Ensure 'table_1' exists for the get_grad_postgrad_data function
                if 'table_1' in tables_dict:
                    grad_postgrad_data = get_grad_postgrad_data(tables_dict)
                else:
                    grad_postgrad_data = {"Graduation GPA": np.nan, "Postgraduation GPA": np.nan, "Affiliations": []}

                combined_data = applicant_info | grad_postgrad_data
                all_results.append(combined_data)
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    df = pd.DataFrame(all_results)
    df.to_csv("applicant_data.csv", index=False)
    print("Data saved to applicant_data.csv")

if __name__ == "__main__":
    main()