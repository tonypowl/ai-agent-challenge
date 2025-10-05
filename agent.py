#take input -> --target _bank_name_ (in this case the icici files)
#check the files in data folder (.pdf) and generates a icici_parser.py with a parse() function
#import the new parse funtion run it on the .pdf and compare the new csv with the old csv
#if inaccurate then retry atmost of 3 times

#nodes: plan (check for files) - generate_code (obtain parse func) - run_tests (compare with old csv) - self_fix (if inaccurate and try<=3)

import os  # directory related tasks
import importlib.util  # calling parse()
import pandas as pd  # dataframe

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from typing import Annotated
from typing_extensions import TypedDict
from typing import Optional

from dotenv import load_dotenv
load_dotenv()  # corrected call

#calling the api request 
import requests

def init_llm(prompt: str, agent="gemini") -> str:
    import requests, os, json

    api_key = os.getenv("GEMINI_API_KEY")
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    model = "models/gemini-2.0-flash-exp"
    print(f"[INFO] Using Gemini model: {model}")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048
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
    """Write the generated parser code to a file."""
    os.makedirs("custom_parsers", exist_ok=True)
    file_path = f"custom_parsers/{target}_parser.py"
    
    #handle the error of output being wrapped in '''....'''
    code = code.replace('```python\n', '').replace('\n```', '').replace('```', '')
    
    with open(file_path, "w") as f:
        f.write(code)
    return file_path

def import_parser(file_path):
    spec = importlib.util.spec_from_file_location("parser_module", file_path)
    parser_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser_module)
    return parser_module

def test_parser(parser_module, pdf_path, csv_path):
    expected_df = pd.read_csv(csv_path)
    parsed_df = parser_module.parse(pdf_path)
    
    if parsed_df.equals(expected_df):
        return True, "Success"
    
    #mismatch information error handling
    issues = []
    if list(parsed_df.columns) != list(expected_df.columns):
        issues.append(f"Column mismatch. Expected: {list(expected_df.columns)}, Got: {list(parsed_df.columns)}")
    if parsed_df.shape != expected_df.shape:
        issues.append(f"Shape mismatch. Expected: {expected_df.shape}, Got: {parsed_df.shape}")
    if not issues:
        issues.append("Data values don't match expected CSV")
    
    return False, "; ".join(issues)

class State(TypedDict):
    messages: Annotated[list, add_messages] # langgraph standard format
    attempt: int
    max_attempts: int
    target: str
    agent: str
    pdf_path: str
    csv_path: str
    parser_file: Optional[str]
    flag: Optional[str]

graph_builder = StateGraph(State)

#node definitions 
def plan(state: State):
    state["messages"].append(
        {"role": "system", "content": "Planning done: assuming PDF & CSV exist."}
    )
    return state

def generate_code(state: State):
    prompt = f"""You are writing Python code directly to a .py file. Do not use markdown formatting.
Write a parser function for {state['target']} bank statement PDF:
Requirements:
- Function: parse(pdf_path: str) -> pd.DataFrame
- PDF format: "Date Description Debit Amt Credit Amt Balance"  
- Return DataFrame with columns: Date, Description, Debit Amt, Credit Amt, Balance
- Skip header lines
- For debit transactions: put amount in 'Debit Amt', leave 'Credit Amt' as empty string
- For credit transactions: put amount in 'Credit Amt', leave 'Debit Amt' as empty string  
- Balance is always last number on line
- Use pdfplumber to extract text
Your response will be written directly to a Python file. Start with import statements."""
    
    code = init_llm(prompt, agent=state["agent"])
    file_path = write_parser(code, state["target"])
    state["parser_file"] = file_path
    state["messages"].append({"role":"system","content":"Parser code generated"})
    return state

def run_tests(state: State):
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

Fix the parse(pdf_path: str) -> pd.DataFrame function.
MUST return DataFrame with exactly these columns: Date, Description, Debit Amt, Credit Amt, Balance

Common issues to fix:
- Wrong column names or count
- Not handling empty debit/credit properly (use empty string "")
- Not skipping header lines
- Balance not being last field
- Description not capturing multiple words

Return complete Python code without any formatting."""
        code = init_llm(fix_prompt, agent=state["agent"])
        state["parser_file"] = write_parser(code, state["target"])
        state["messages"].append(
            {"role":"system","content":f"Parser self-fix attempt {state['attempt']}"}
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
    parser.add_argument("--llm", choices=["gemini","groq"], default="gemini")
    args = parser.parse_args()

    pdf_path = f"data/{args.target}/{args.target} sample.pdf"
    csv_path = f"data/{args.target}/result.csv"

    initial_state = {
        "messages": [],
        "attempt": 0,
        "max_attempts": 3,
        "target": args.target,
        "agent": args.llm,
        "pdf_path": pdf_path,
        "csv_path": csv_path,
        "parser_file": None,
        "flag": None
    }

    final_state = graph.invoke(initial_state)
    print("[INFO] Agent finished. Messages log:")
    for msg in final_state["messages"]:
        if hasattr(msg, 'content'):
            print(msg.content)
        else:
            print(msg)
