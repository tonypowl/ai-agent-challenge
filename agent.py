#take input -> --target _bank_name_ (in this case the icici files)
#check the files in data folder (.pdf) and generates a icici_parser.py with a parse() function
#import the new parse funtion run it on the .pdf and compare the new csv with the old csv
#if inaccurate then retry atmost of 3 times
import os  # directory related tasks
import importlib.util  # calling parse()
import pandas as pd  # dataframe
import requests, json #calling the api request, json formatting for api interaction 

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict
from typing import Optional
from dotenv import load_dotenv
load_dotenv()  # corrected call

#constants
MAX_ATTEMPTS = 3
MAX_OUTPUT_TOKENS = 2048
TEMPERATURE = 0.2
GEMINI_MODEL = "models/gemini-2.0-flash-exp"

def init_llm(prompt: str, agent="gemini") -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    model = GEMINI_MODEL

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": TEMPERATURE,
            "maxOutputTokens": MAX_OUTPUT_TOKENS
        }
    }

    gen_url = f"{base_url}/{model}:generateContent?key={api_key}"
    response = requests.post(
        gen_url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

def write_parser(code: str, target: str) -> str:
    os.makedirs("custom_parsers", exist_ok=True)
    file_path = f"custom_parsers/{target}_parser.py"
    #handle the error of output being wrapped in '''....'''
    code = code.replace('```python\n', '').replace('\n```', '').replace('```', '')

    with open(file_path, "w") as f:
        f.write(code)
    return file_path

def import_parser(file_path: str) -> any: #getting the parse() function from the generated .py 
    spec = importlib.util.spec_from_file_location("parser_module", file_path)
    parser_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser_module)
    return parser_module

def test_parser(parser_module: any, pdf_path: str, csv_path: str) -> tuple[bool, str]:
    expected_df = pd.read_csv(csv_path)
    
    #exception handling to check if the parsing worked 
    try:
        parsed_df = parser_module.parse(pdf_path)
    except Exception as e:
        return False, f"parser execution failed: {str(e)}"
    if not isinstance(parsed_df, pd.DataFrame):
        return False, "parse() must return a DataFrame"
    if parsed_df.equals(expected_df):
        return True, "success" #comparison for better error messages
    
    #mismatch information error handling
    issues = []
    if list(parsed_df.columns) != list(expected_df.columns):
        issues.append(f"Column mismatch. Expected: {list(expected_df.columns)}, Got: {list(parsed_df.columns)}")
    if parsed_df.shape != expected_df.shape:
        issues.append(f"Shape mismatch. Expected: {expected_df.shape}, Got: {parsed_df.shape}")
    else:
        issues.append(f"Data mismatch. Expected: {expected_df.shape}, Got: {parsed_df.shape} (same shape, different values)")
    return False, "; ".join(issues)

class State(TypedDict): #langgraph standard format for creating a state 
    messages: Annotated[list, add_messages] 
    attempt: int
    max_attempts: int
    target: str
    agent: str
    pdf_path: str
    csv_path: str
    parser_file: Optional[str]
    flag: Optional[str]
graph_builder = StateGraph(State)

#nodes: plan (check for files) - generate_code (obtain parse func) - run_tests (compare with old csv) - self_fix (if inaccurate and try<=3)
def plan(state: State) -> State:
    state["messages"].append(
        {"role": "system", "content": "Planning done: assuming PDF & CSV exist."}
    )
    return state

def generate_code(state: State):
    prompt = f"""You are writing Python code directly to a .py file make sure not use markdown formatting.
Write a parser function for {state['target']} bank statement PDF:
my requirements are:
analyze the pdf structure first, then choose best parsing approach
use appropriate libraries for pdf parsing (you decide what works best)
Function: parse(pdf_path: str) -> pd.DataFrame
PDF format: "Date Description Debit Amt Credit Amt Balance", thats the sample one go through the pdf and see what columns are there 
return DataFrame with columns: Date, Description, Debit Amt, Credit Amt, Balance add or remove anything according to the file 
skip header lines, make sure you can make a code that can assess the file and make changes accordinlgly 
for debit transactions: put amount in 'Debit Amt', leave 'Credit Amt' as empty string 
for credit transactions: put amount in 'Credit Amt', leave 'Debit Amt' as empty string
make sure that you dont put all transactions only in one column, assign the debit ones to the debit and credit ones to credit  
balance is always last number on line
When parsing dates, use: pd.to_datetime(date_string, format='%d-%m-%Y', errors='coerce') to avoid warnings
write the response directly into a Python file. Start with import statements.
IMPORTANT: Handle decimal amounts correctly:
amounts contain decimals like 3886.08, 1652.61 etc
do not convert amounts to integers or remove decimals, do not use predefined lists for amount matching
parse amounts as float values: float(amount_string), keep original decimal precision in the dataframe"""
    
    code = init_llm(prompt, agent=state["agent"])
    file_path = write_parser(code, state["target"])
    state["parser_file"] = file_path
    state["messages"].append({"role":"system","content":"Parser code generated"})
    return state

def run_tests(state: State) -> State:
    parser_module = import_parser(state["parser_file"])
    success, msg = test_parser(parser_module, state["pdf_path"], state["csv_path"])
    state["messages"].append({"role":"system","content":f"Test result: {msg}"})
    state["flag"] = None if success else msg
    return state

# retry loop inside self_fix
def self_fix(state: State):
    while state["flag"] and state["attempt"] < state["max_attempts"]:
        state["attempt"] += 1
        fix_prompt = f"""
The parser failed: {state['flag']}
fix the parse(pdf_path: str) -> pd.DataFrame function.
MUST return DataFrame with exactly these columns: Date, Description, Debit Amt, Credit Amt, Balance or whatever is present in the scanned pdf 
analyze what went wrong and choose better approach:
- wrong row count? check pdf extraction method
- missing columns? verify dataframe structure  
- empty columns? check debit/credit assignment logic
- parsing errors? try different pdf reading approach
extract all transactions (target: 100 rows)
debit amounts go in 'Debit Amt' column, credit amounts in 'Credit Amt' column
common issues to fix:
- wrong column names or count
- not handling empty debit/credit properly (use empty string "") and make sure to assign them correctly, make sure that every transaction is accounted for 
- not skipping header lines
- balance not being last field, description not capturing multiple words
- make sure if its a debit transaction then the credit field is kept empty, likewise if its a credit transaction then the debit should be kept empty  
- Use pd.to_datetime(date_string, format='%d-%m-%Y', errors='coerce') for date parsing to avoid warnings
return complete Python code without any formatting.
if getting "'38868' is not in list" errors:
do not use predefined lists for amount validation, parse amounts as floats directly: float(amount_text)
do not remove decimal points from amounts, amounts should be stored as numeric values, not strings"""
        code = init_llm(fix_prompt, agent=state["agent"])
        state["parser_file"] = write_parser(code, state["target"])
        state["messages"].append(
            {"role":"system","content":f"parser self-fix attempt {state['attempt']}"}
        )
        # run tests again after fixing
        parser_module = import_parser(state["parser_file"])
        success, msg = test_parser(parser_module, state["pdf_path"], state["csv_path"])
        state["messages"].append({"role":"system","content":f"Test result: {msg}"})
        state["flag"] = None if success else msg
    return state

#adding nodes
graph_builder.add_node("plan", plan)
graph_builder.add_node("generate_code", generate_code)
graph_builder.add_node("run_tests", run_tests)
graph_builder.add_node("self_fix", self_fix)
#edges between nodes
graph_builder.add_edge(START, "plan")
graph_builder.add_edge("plan", "generate_code")
graph_builder.add_edge("generate_code", "run_tests")
graph_builder.add_edge("run_tests", "self_fix")
graph_builder.add_edge("self_fix", END) 
#final compilation of the graph
graph = graph_builder.compile()

#cli
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--llm", choices=["gemini","groq"], default="gemini") #choice of agent incase gemini fails 
    args = parser.parse_args()

    pdf_path = f"data/{args.target}/{args.target} sample.pdf"
    csv_path = f"data/{args.target}/result.csv"

    initial_state = {
        "messages": [],
        "attempt": 0,
        "max_attempts": MAX_ATTEMPTS,
        "target": args.target,
        "agent": args.llm,
        "pdf_path": pdf_path,
        "csv_path": csv_path,
        "parser_file": None,
        "flag": None
    }
    print(f"starting AI agent for {args.target} bank statement parsing...")
    final_state = graph.invoke(initial_state)
    
    #output messages to see the results 
    print(f"\nAgent completed with {final_state['attempt']} self-fix attempts\n")
    if final_state['flag']:
        print(f"final result:- {final_state['flag']}\n")
    else:
        print("parser generated successfully!")
    if final_state['parser_file']:
        print(f"generated: {final_state['parser_file']}")
        print(f"self-fix attempts: {final_state['attempt']}/{final_state['max_attempts']}")
    

