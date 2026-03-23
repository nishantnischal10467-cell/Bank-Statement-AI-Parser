import argparse
import os
import sys

from core.parser_agent import BankParserAgent


def main():
    parser = argparse.ArgumentParser(
        description="AI Agent for generating custom bank statement parsers"
    )
    parser.add_argument(
        "--target", 
        required=True,
        help="Target bank name (e.g., icici, sbi, hdfc)"
    )
    parser.add_argument(
        "--pdf", 
        help="Path to specific PDF file to parse with existing parser"
    )
    
    args = parser.parse_args()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=your_api_key")
        sys.exit(1)
    
    agent = BankParserAgent()
    success = agent.run(args.target.lower(), args.pdf)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
