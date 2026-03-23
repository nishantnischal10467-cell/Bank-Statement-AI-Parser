from typing import Dict, Any, Optional, TypedDict


class AgentState(TypedDict):
    target_bank: str
    pdf_path: str
    csv_path: str
    parser_code: Optional[str]
    test_results: Optional[Dict[str, Any]]
    attempt_count: int
    max_attempts: int
    error_message: Optional[str]
    success: bool
