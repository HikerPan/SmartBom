from crewai import Agent
from langchain_openai import ChatOpenAI
from src.config import API_KEY, API_BASE, MODEL_NAME
from src.tools import inventory_search_tool, history_search_tool

# Initialize LLM
llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=API_BASE
)

# Define the Agent
bom_matcher_agent = Agent(
    role='BOM Normalization Expert',
    goal='Find the most accurate ERP inventory code for a given raw BOM component.',
    backstory="""
    You are an expert in electronic components and BOM management. 
    You have access to a historical database of previous matches and a current ERP inventory.
    
    Your decision process is strictly defined:
    1. **Check History First**: Use the History Search Tool. If it returns a "FOUND" result with a high confidence match, use that code immediately and stop.
    2. **Check Inventory Second**: If history doesn't yield a perfect match, use the Inventory Search Tool. Compare the raw description (Value, Footprint, Description) with the candidates. 
       - Pay attention to "R" or "C" prefixes in footprints (e.g., R0603 vs 0603 are the same).
       - Ignore suffixes like "_1%" in values.
    3. **Fallback**: If you cannot find a confident match in either history or inventory, output "MANUAL_CHECK".
    
    You must output ONLY the ERP Code if found, or "MANUAL_CHECK".
    """,
    tools=[history_search_tool, inventory_search_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False
)
