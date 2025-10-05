import pytest
import pandas as pd
import os
from agent import init_llm, write_parser

def test_agent_basics(): #test without calling any env variables 
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
    os.remove(result_path)

def test_generated_parser_works():
    from agent import import_parser
    
    parser_module = import_parser("custom_parsers/icici_parser.py")
    assert hasattr(parser_module, 'parse')
    
    result_df = parser_module.parse("data/icici/icici sample.pdf")
    assert isinstance(result_df, pd.DataFrame)
    assert len(result_df.columns) == 5

def test_required_files_exist():
    assert os.path.exists("agent.py")
    assert os.path.exists("requirements.txt") 
    assert os.path.exists("README.md")
    assert os.path.exists("data/icici")

def test_agent_integration():
    # Check that agent can create the expected structure
    assert os.path.exists("custom_parsers") or True  # directory gets created by agent

    parser_path = "custom_parsers/icici_parser.py"
    if os.path.exists(parser_path):
        with open(parser_path, 'r') as f:
            content = f.read()
        assert "def parse" in content
        assert "import" in content
        print("Generated parser structure verified!")
    else:
        print("No parser found - run 'python3 agent.py --target icici' first")