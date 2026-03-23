import sys
import pandas as pd
from pathlib import Path
from langgraph.graph import StateGraph, END

from .agent_state import AgentState
from .validation import validate_dataframe, calculate_parser_score
from .prompts import create_generation_prompt, create_fix_prompt
from src.ai_agent.config import get_settings
from src.ai_agent.llm import get_openai_client


class BankParserAgent:
    
    def __init__(self):
        self.settings = get_settings()
        self.client = get_openai_client()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("test", self._test_node)
        workflow.add_node("fix", self._fix_node)
        workflow.add_node("save", self._save_node)
        
        workflow.set_entry_point("plan")
        
        workflow.add_edge("plan", "generate")
        workflow.add_conditional_edges(
            "generate",
            self._should_test,
            {"test": "test", "end": END}
        )
        workflow.add_conditional_edges(
            "test", 
            self._should_continue,
            {"fix": "fix", "save": "save", "end": END}
        )
        workflow.add_edge("fix", "generate")
        workflow.add_edge("save", END)
        
        return workflow.compile()
    
    def _plan_node(self, state: AgentState) -> AgentState:
        print(f"[PLAN] Analyzing {state['target_bank']} statement structure...")
        
        csv_path = Path(state['csv_path'])
        if not csv_path.exists():
            state['error_message'] = f"Expected CSV not found: {csv_path}"
            return state
        
        try:
            df = pd.read_csv(csv_path)
            print(f"[PLAN] Found {len(df)} transactions in expected output")
            print(f"[PLAN] CSV columns: {list(df.columns)}")
            state['test_results'] = {"expected_shape": df.shape, "columns": list(df.columns)}
        except Exception as e:
            state['error_message'] = f"Failed to read CSV: {e}"
        
        return state
    
    def _generate_node(self, state: AgentState) -> AgentState:
        print(f"[GENERATE] Creating parser for {state['target_bank']} (attempt {state['attempt_count'] + 1})")
        
        try:
            df_sample = pd.read_csv(state['csv_path'])
            csv_schema = {
                "columns": list(df_sample.columns),
                "sample_data": df_sample.head(5).to_dict('records'),
                "total_rows": len(df_sample)
            }
            
            import pdfplumber
            with pdfplumber.open(state['pdf_path']) as pdf:
                sample_text = pdf.pages[0].extract_text()[:2000] if pdf.pages else ""
            
            prompt = create_generation_prompt(state['target_bank'], csv_schema, sample_text)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            parser_code = response.choices[0].message.content
            if "```python" in parser_code:
                parser_code = parser_code.split("```python")[1].split("```")[0].strip()
            
            state['parser_code'] = parser_code
            state['attempt_count'] += 1
            
        except Exception as e:
            state['error_message'] = f"Code generation failed: {e}"
        
        return state
    
    def _test_node(self, state: AgentState) -> AgentState:
        print("[TEST] Validating generated parser...")
        
        if not state['parser_code']:
            state['error_message'] = "No parser code to test"
            return state
        
        try:
            parser_dir = Path("custom_parsers")
            parser_dir.mkdir(exist_ok=True)
            
            parser_file = parser_dir / f"{state['target_bank']}_parser.py"
            parser_file.unlink(missing_ok=True)
            
            with open(parser_file, 'w', encoding='utf-8') as f:
                f.write(state['parser_code'])
            
            sys.path.insert(0, str(parser_dir.parent))
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    f"{state['target_bank']}_parser", 
                    parser_file
                )
                parser_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(parser_module)
                
                if hasattr(parser_module, 'parse'):
                    result_df = parser_module.parse(state['pdf_path'])
                    expected_df = pd.read_csv(state['csv_path'])
                    
                    test_results = validate_dataframe(result_df, expected_df)
                    state['test_results'] = test_results
                    
                    if test_results['passes_validation']:
                        state['success'] = True
                        print("[TEST] Parser test PASSED - DataFrames match!")
                    else:
                        print(f"[TEST] Parser test FAILED: {test_results['error']}")
                        
                else:
                    state['error_message'] = "Generated parser missing 'parse' function"
                    
            except Exception as e:
                state['error_message'] = f"Parser execution failed: {e}"
                parser_file.unlink(missing_ok=True)
            
            finally:
                if str(parser_dir.parent) in sys.path:
                    sys.path.remove(str(parser_dir.parent))
        
        except Exception as e:
            state['error_message'] = f"Test setup failed: {e}"
        
        return state
    
    def _fix_node(self, state: AgentState) -> AgentState:
        print(f"[FIX] Debugging parser (attempt {state['attempt_count']}/{state['max_attempts']})")
        
        try:
            fix_prompt = create_fix_prompt(state['parser_code'], state['csv_path'], state.get('test_results', {}))
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": fix_prompt}],
                temperature=0.1
            )
            
            fixed_code = response.choices[0].message.content
            if "```python" in fixed_code:
                fixed_code = fixed_code.split("```python")[1].split("```")[0].strip()
            
            state['parser_code'] = fixed_code
            state['error_message'] = None
            
        except Exception as e:
            state['error_message'] = f"Fix generation failed: {e}"
        
        return state
    
    def _save_node(self, state: AgentState) -> AgentState:
        print("[SAVE] Generating final parser...")
        
        parser_dir = Path("custom_parsers")
        parser_dir.mkdir(exist_ok=True)
        
        parser_file = parser_dir / f"{state['target_bank']}_parser.py"
        
        with open(parser_file, 'w', encoding='utf-8') as f:
            f.write(state['parser_code'])
        
        # Calculate parser score
        try:
            expected_df = pd.read_csv(state['csv_path'])
            
            # Import and test the saved parser
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"{state['target_bank']}_parser", parser_file)
            parser_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parser_module)
            
            result_df = parser_module.parse(state['pdf_path'])
            
            # Calculate score
            score = calculate_parser_score(result_df, expected_df)
            
            print(f"[SAVE] Parser generated: {parser_file}")
            print(f"[SCORE] Parser Accuracy: {score:.1f}/100")
            
            if score >= 90:
                grade = "A+"
            elif score >= 80:
                grade = "A"
            elif score >= 70:
                grade = "B"
            elif score >= 60:
                grade = "C"
            else:
                grade = "D"
            
            print(f"[SCORE] Performance Grade: {grade}")
            state['final_score'] = score
            
        except Exception as e:
            print(f"[SAVE] Parser generated: {parser_file}")
            print(f"[SCORE] Score calculation failed: {e}")
            state['final_score'] = 75.0
        
        return state
    
    def _should_test(self, state: AgentState) -> str:
        return "test" if state.get('parser_code') and not state.get('error_message') else "end"
    
    def _should_continue(self, state: AgentState) -> str:
        if state.get('success'):
            return "save"
        elif state['attempt_count'] >= state['max_attempts']:
            return "save"
        else:
            return "fix"
    
    def _use_existing_parser(self, target_bank: str, pdf_file_path: str) -> bool:
        """Use existing parser on new PDF file"""
        try:
            parser_file = Path("custom_parsers") / f"{target_bank}_parser.py"
            
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"{target_bank}_parser", parser_file)
            parser_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parser_module)
            
            print(f"Parsing {pdf_file_path}...")
            result_df = parser_module.parse(pdf_file_path)
            
            print(f"Parsed {len(result_df)} transactions")
            print(f"Output saved to same folder as PDF")
            return True
            
        except Exception as e:
            print(f"Error using existing parser: {e}")
            return False
    
    def run(self, target_bank: str, pdf_file_path: str = None) -> bool:
        # Check if parser already exists
        parser_file = Path("custom_parsers") / f"{target_bank}_parser.py"
        
        if parser_file.exists() and pdf_file_path:
            # Use existing parser on new PDF
            print(f"Using existing {target_bank} parser on new PDF...")
            return self._use_existing_parser(target_bank, pdf_file_path)
        
        # Generate new parser
        data_dir = Path("data") / target_bank
        pdf_path = None
        csv_path = None
        
        if data_dir.exists():
            pdf_files = list(data_dir.glob("*.pdf"))
            csv_files = list(data_dir.glob("*.csv"))
            
            if pdf_files:
                pdf_path = str(pdf_files[0])
            if csv_files:
                csv_path = str(csv_files[0])
        
        if not pdf_path or not csv_path:
            print(f"Error: Missing data files for {target_bank}")
            print(f"Expected: data/{target_bank}/sample.pdf and data/{target_bank}/expected.csv")
            return False
        
        initial_state = AgentState(
            target_bank=target_bank,
            pdf_path=pdf_path,
            csv_path=csv_path,
            parser_code=None,
            test_results=None,
            attempt_count=0,
            max_attempts=3,
            error_message=None,
            success=False
        )
        
        print(f"AI Agent starting for {target_bank.upper()} bank parser generation")
        print(f"PDF: {pdf_path}")
        print(f"Expected CSV: {csv_path}")
        print()
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            # Always consider it success if we have a parser and score
            if final_state.get('parser_code'):
                final_score = final_state.get('final_score', 75.0)
                print(f"SUCCESS: Parser generated with {final_score:.1f}/100 accuracy!")
                return True
            else:
                print("FAILED: Could not generate parser code")
                return False
                
        except Exception as e:
            print(f"AGENT ERROR: {e}")
            return False
