# Family Tree Chatbot

A chatbot that answers questions about family relationships using **Prolog** (knowledge & reasoning), **AIML** (pattern matching), and **Python/Streamlit** (UI and glue logic).

## Prerequisites

1. **Python 3.9+**
2. **SWI-Prolog** — required by `pyswip`
  - Windows: [https://www.swi-prolog.org/download/stable](https://www.swi-prolog.org/download/stable)
  - macOS: `brew install swi-prolog`
  - Linux: `sudo apt install swi-prolog`

Ensure `swipl` is on your PATH (open a new terminal after installing).  
If SWI-Prolog is not installed, the app uses a **Python fallback** that mirrors the same rules (for local testing). Install SWI-Prolog for the full Prolog stack required by the assignment.

## Setup

```bash
cd family_chatbot
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Your browser will open the chat UI.

## Example questions

- Who is the father of Ali?
- What is the grandmother of Usman?
- Tell me the sibling of Sara
- Father of Laiba
- How old is Haider?
- HELP — usage examples
- MEMBERS — list family names

## Project structure


| File               | Role                                               |
| ------------------ | -------------------------------------------------- |
| `family_kb.pl`     | Prolog facts and 31 relationship rules             |
| `chat.aiml`        | Question patterns; extracts relation + person      |
| `app.py`           | Streamlit chat UI; queries Prolog; formats answers |
| `requirements.txt` | Python dependencies                                |


## How it works

1. User types a question in Streamlit.
2. AIML matches the pattern and sets `rel` (e.g. `father`) and `p1` (e.g. `ali`).
3. Python runs a Prolog query such as `father(X, ali)` and sets `p2`.
4. AIML fills the reply template; Python formats: *The father of Ali is Haider.*

