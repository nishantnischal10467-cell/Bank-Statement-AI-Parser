AI Bank Statement Parser Agent
Overview

This project builds an AI-powered agent that automatically creates bank statement parsers from PDF files.
It learns from a sample PDF and its matching CSV, then generates reusable parsers for the same bank.

Features
Auto-generates parsers using AI
Works with different bank formats
Self-corrects errors during parsing
Outputs clean CSV with correct structure
Reuses existing parsers for faster processing
Setup
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Add API key
set OPENAI_API_KEY=your_api_key
Usage
1. Generate a Parser
python agent.py --target icici

Requires:

data/icici/sample.pdf
data/icici/result.csv
2. Parse a New Statement
python agent.py --target icici --pdf data/icici/statement.pdf
3. Add New Bank
Create folder: data/<bank>/
Add sample PDF + CSV
Run the generate command
How It Works

The agent follows a simple loop:

Analyze sample PDF + CSV
Generate parser code
Test accuracy
Fix errors automatically
Save working parser
Project Structure
agent.py
core/
data/
custom_parsers/
src/
requirements.txt
Tech Stack
Python
LangGraph
OpenAI API
Pandas
PDF processing tools
