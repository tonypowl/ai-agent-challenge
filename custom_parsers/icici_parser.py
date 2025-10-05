import pdfplumber
import pandas as pd

def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parses a PDF file and extracts data into a Pandas DataFrame.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        pd.DataFrame: A DataFrame with columns 'Date', 'Description', 'Debit Amt', 'Credit Amt', and 'Balance'.
                      Returns an empty DataFrame if parsing fails.
    """
    data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            # Attempt to parse date
                            pd.to_datetime(parts[0], errors='raise')

                            date = parts[0]
                            balance = parts[-1]
                            debit = ""
                            credit = ""
                            description_start_index = 1
                            
                            # Check if debit and credit amounts are present before balance
                            try:
                                float(parts[-2].replace(',', ''))  # Check if the second to last part is a number
                                if len(parts) >= 5:
                                    try:
                                        float(parts[-3].replace(',', ''))
                                        debit = parts[-3].replace(',', '')
                                        credit = parts[-2].replace(',', '')
                                        description_start_index = 1
                                    except ValueError:
                                        credit = parts[-2].replace(',', '')
                                        description_start_index = 1
                                        
                                else:
                                    credit = parts[-2].replace(',', '')
                                    description_start_index = 1
                            except ValueError:
                                pass  # No debit/credit found before balance

                            description = " ".join(parts[description_start_index:len(parts) - 1 if credit or debit else len(parts)])

                            data.append([date, description, debit, credit, balance])
                        except ValueError:
                            # Skip lines that don't start with a date
                            pass

    df = pd.DataFrame(data, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
    return df