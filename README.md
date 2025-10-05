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

<img width="153" height="531" alt="langgraph_structure" src="https://github.com/user-attachments/assets/13cd2fb3-d759-43c3-b2dc-0f83c32b449a" />


