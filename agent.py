#take input -> --target _bank_name_ (in this case the icici files)
#check the files in data folder (.pdf) and generates a icic_parser.py with a parse() function 
#import the new parse funtion run it on the .pdf and compare the new csv with the old csv 
#if inaccurate then retry atmost of 3 times

#nodes : plan (check for files) - generate_code (obtain parse func) - run_tests (compare with old csv) - self_fix (if inaccurate and try<=3)

import os #directory related tasks 
import importlib.util #calling parse() 
import pandas as pd #dataframe 
import requests #api call 

from langgraph.graph import StateGraph, START, END 
from langgraph.graph.message import add_messages 

from typing import Annotated
from typing_extensions import TypedDict
from typing import Optional

from dotenv import load_dotenv 
load_dotenv

class State(TypedDict):
    messages: Annotated[list, add_messages] #langgraph stndrd format
    attempt: int 
    max_attempts: int 
    target: str 
    agent: str 
    pdf_path: str 
    csv_path: str 
    parser_file: Optional[str]
    flag: Optional[str]

graph_builder = StateGraph(State)

#nodes 
def plan():
    pass

def generate_code():
    pass 

def run_tests():
    pass 

def self_fix():
    pass 






