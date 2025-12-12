from crewai import Agent, LLM
# from langchain_openai import ChatOpenAI
from src.config import API_KEY, API_BASE, MODEL_NAME
from src.tools import inventory_search_tool, history_search_tool

# Initialize LLM
# Using crewai.LLM with explicit openai/ prefix for litellm
llm = LLM(
    model=f"openai/{MODEL_NAME}",
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
    1. **Check Inventory First**: Use the Inventory Search Tool with the structured query (e.g., "Value:xxx|Footprint:yyy"). 
       - If it returns a match with high confidence (matching Value and Footprint), use that code immediately.
       - Explicitly state "Source: Inventory" in your final answer.
    2. **Check History Second**: If Inventory doesn't yield a perfect match, use the History Search Tool.
       - If it returns a "FOUND" result, use that code.
       - Explicitly state "Source: History" in your final answer.
    3. **Fallback**: If you cannot find a confident match in either, output "MANUAL_CHECK".
    
    You must output ONLY the ERP Code if found (plus source), or "MANUAL_CHECK".
    Example Final Answer: "142800041 (Source: Inventory)"
    """,
    tools=[history_search_tool, inventory_search_tool],
    llm=llm,
    verbose=True,
    allow_delegation=False
)
