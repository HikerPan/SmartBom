from crewai.tools import BaseTool
from langchain_chroma import Chroma
from src.vector_store import embeddings, CHROMA_DB_DIR

# Initialize Vector Stores for direct access (to get scores)
inventory_store = Chroma(
    collection_name="inventory",
    embedding_function=embeddings,
    persist_directory=CHROMA_DB_DIR
)

history_store = Chroma(
    collection_name="history",
    embedding_function=embeddings,
    persist_directory=CHROMA_DB_DIR
)

from src.utils import load_data
import pandas as pd

# Load inventory data for exact matching
try:
    df_inventory = load_data("data/inventory.xlsx")
    print(f"Loaded {len(df_inventory)} inventory items for exact matching.")
except Exception as e:
    print(f"Warning: Could not load inventory.xlsx for exact matching: {e}")
    df_inventory = pd.DataFrame()

class InventorySearchTool(BaseTool):
    name: str = "Inventory Search Tool"
    description: str = "Search for components in the ERP inventory. Input can be a structured string 'Value:xxx|Footprint:yyy' or a plain text query."

    def _run(self, query: str) -> str:
        # 1. Try Structured Exact/Partial Match using Pandas
        if "Value:" in query and "Footprint:" in query:
            try:
                # Parse query "Value:0.1uF|Footprint:0402"
                parts = query.split("|")
                val_part = [p for p in parts if p.startswith("Value:")][0]
                fp_part = [p for p in parts if p.startswith("Footprint:")][0]
                
                val = val_part.split(":", 1)[1].strip()
                fp = fp_part.split(":", 1)[1].strip()
                
                if not df_inventory.empty:
                    # Filter logic: Name contains Value AND Spec contains Footprint
                    # Using string contains for flexibility
                    matches = df_inventory[
                        df_inventory['存货名称'].astype(str).str.contains(val, case=False, regex=False) & 
                        df_inventory['规格型号'].astype(str).str.contains(fp, case=False, regex=False)
                    ]
                    
                    if not matches.empty:
                        # Return top 3 matches
                        formatted_results = []
                        for _, row in matches.head(3).iterrows():
                            content = f"名称: {row.get('存货名称', '')}, 规格: {row.get('规格型号', '')}, 供应商: {row.get('主要供货单位名称', '')}"
                            metadata = {"code": str(row.get('存货编码', '')), "spec": str(row.get('规格型号', ''))}
                            formatted_results.append(f"Source: Inventory (Exact Match) | Content: {content} | Metadata: {metadata}")
                        return "\n".join(formatted_results)
            except Exception as e:
                print(f"Structured search failed: {e}")

        # 2. Fallback to Vector Search
        results = inventory_store.similarity_search_with_score(query, k=3)
        
        if not results:
            return "No matching components found in inventory."
            
        formatted_results = []
        for doc, score in results:
            content = doc.page_content
            metadata = doc.metadata
            formatted_results.append(f"Source: Inventory (Vector Search) | Content: {content} | Metadata: {metadata}")
            
        return "\n".join(formatted_results)

class HistorySearchTool(BaseTool):
    name: str = "History Search Tool"
    description: str = "Search for previously matched BOM items. Input should be the raw component string."

    def _run(self, query: str) -> str:
        # Search Top 1
        # We need relevance score.
        results = history_store.similarity_search_with_relevance_scores(query, k=1)
        
        if not results:
            return "NOT_FOUND"
            
        doc, score = results[0]
        
        # Guide says: score > 0.95
        if score > 0.95:
            # Extract code from text "原始输入: ... => 最终编码: {matched_code}"
            # Or just return the whole text and let Agent parse it.
            # The guide says "return FOUND: {code}".
            text = doc.page_content
            try:
                # Naive parse, or just return the text which contains the code.
                # Let's return the text prefixed with FOUND if high score.
                return f"Source: History | FOUND: {text}"
            except:
                return f"Source: History | FOUND: {text}"
        else:
            return "NOT_FOUND"

# Instantiate tools
inventory_search_tool = InventorySearchTool()
history_search_tool = HistorySearchTool()
