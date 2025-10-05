# ai-agent-challenge
Coding agent challenge which write custom parsers for Bank statement PDF.

### Step 1: Install Dependencies
```
pip3 install -r requirements.txt
```

### Step 2: Set API Key
Create `.env` file:
```
GEMINI_API_KEY=your_api_key_here
```

### Step 3: Verify Data
Check `data/icici/` contains:
- `icici sample.pdf` 
- `result.csv`

### Step 4: Run Agent
```bash
python3 agent.py --target icici
```

### Step 5: Check Output
Generated parser at `custom_parsers/icici_parser.py` with `parse()` function.


The first node is the default START node which connected to plan node whcih makes sure that the required files, folders and packages exist then it 
moves on to the generate_code node that consists of the prompt sent to the ai agent to create a parser code after which run_tests imports the newly created parser and verifies it by comparing it with the sample PDF and the expected CSV. If any errors are found then it enters the self_fix node, which calls a retry loop where the AI agent is prompted to correct the parser. 
The loop continues <= 3 times as per the challenges instructions

<img width="153" height="531" alt="langgraph_structure" src="https://github.com/user-attachments/assets/13cd2fb3-d759-43c3-b2dc-0f83c32b449a" />


