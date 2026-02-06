import sys
from pathlib import Path
import os
import asyncio
from dotenv import load_dotenv

# Add orchestrator to path
orchestrator_base = Path("/Users/pawanpandey/Documents/french_admission_workflow-main/master_orchestrator_agent/src")
if str(orchestrator_base) not in sys.path:
    sys.path.insert(0, str(orchestrator_base))

# Load .env
load_dotenv("/Users/pawanpandey/Documents/french_admission_workflow-main/.env")

from master_orchestrator.adapters.passport_adapter import PassportAgentAdapter
from master_orchestrator.config.settings import Settings

def test_passport_agent():
    print("Testing Passport Agent Adapter...")
    settings = Settings()
    adapter = PassportAgentAdapter(settings)
    
    # Try to initialize
    try:
        adapter._ensure_initialized()
        print("Passport Agent initialized successfully.")
    except Exception as e:
        print(f"FAILED to initialize Passport Agent: {e}")
        return

    # Try to process a dummy file or just check settings
    print(f"Passport API Key (masked): {os.environ.get('PA_OPENAI_API_KEY')[:10]}...")

if __name__ == "__main__":
    test_passport_agent()
