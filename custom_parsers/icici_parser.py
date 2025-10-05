import pdfplumber
import pandas as pd

def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parses a PDF file and extracts data into a Pandas DataFrame.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        pd.DataFrame: A DataFrame containing the extracted data with columns:
                      'Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'.
                      Returns an empty DataFrame if parsing fails.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_data = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines = text.splitlines()
                    for line in lines:
                        # Skip header lines based on keywords
                        if "Date" in line or "Description" in line or "Balance" in line:
                            continue

                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                # Attempt to parse the date
                                date_str = parts[0]
                                date = pd.to_datetime(date_str, format='%d-%m-%Y', errors='coerce')

                                # Extract balance (last element)
                                balance = parts[-1]

                                # Extract debit and credit amounts
                                debit_amt = ""
                                credit_amt = ""
                                if len(parts) >= 5:
                                    try:
                                        float(parts[-2])
                                        credit_amt = parts[-2]
                                        debit_credit_index = -2
                                    except ValueError:
                                        debit_credit_index = -1
                                else:
                                    debit_credit_index = -1
                                
                                if len(parts) >= 5:
                                    try:
                                        float(parts[debit_credit_index-1])
                                        debit_amt = parts[debit_credit_index-1]
                                    except ValueError:
                                        pass

                                # Extract description (everything between date and debit/credit)
                                description = " ".join(parts[1:debit_credit_index-1 if debit_amt else debit_credit_index])

                                # Append the extracted data
                                all_data.append([date_str, description, debit_amt, credit_amt, balance])
                            except ValueError:
                                pass

        # Create DataFrame
        df = pd.DataFrame(all_data, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
        return df

    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])