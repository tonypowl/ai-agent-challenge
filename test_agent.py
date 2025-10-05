import pytest
import pandas as pd
import os
from agent import init_llm, write_parser

def test_agent_basics():
    #test without calling any env variables 
    import os
    assert os.path.exists("agent.py")
    assert "write_parser" in str(write_parser)
    
def test_parser_creation():
    test_code = """import pdfplumber
import pandas as pd

def parse(pdf_path: str) -> pd.DataFrame:
    return pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
"""
    
    # test parser file creation
    result_path = write_parser(test_code, "test_bank")
    assert os.path.exists(result_path)
    assert "test_bank_parser.py" in result_path
    
    # cleanup
    os.remove(result_path)

def test_dataframe_structure():
    df = pd.DataFrame({
        'Date': ['2023-01-01'],
        'Description': ['Test Transaction'],
        'Debit Amt': ['100'],
        'Credit Amt': [''],
        'Balance': ['1000']
    })
    
    # check required columns
    expected_columns = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
    assert list(df.columns) == expected_columns
    assert len(df) == 1

def test_required_files_exist():
    assert os.path.exists("agent.py")
    assert os.path.exists("requirements.txt") 
    assert os.path.exists("README.md")
    assert os.path.exists("data/icici")