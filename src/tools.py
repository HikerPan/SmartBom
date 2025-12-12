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

class InventorySearchTool(BaseTool):
    name: str = "Inventory Search Tool"
    description: str = "Search for components in the ERP inventory. Input should be a string containing component description, footprint, and value."

    def _run(self, query: str) -> str:
        # Search Top 3
        results = inventory_store.similarity_search_with_score(query, k=3)
        
        if not results:
            return "No matching components found in inventory."
            
        formatted_results = []
        for doc, score in results:
            # Chroma returns distance by default for some metrics, but let's assume cosine similarity or convert.
            # However, langchain_chroma default might be L2 or Cosine. 
            # If using default, lower score might be better (distance) or higher is better (similarity).
            # OpenAI embeddings are normalized, so dot product is cosine similarity.
            # Chroma default is usually L2. 
            # Let's assume we just return the content and let the LLM decide, 
            # BUT the guide mentions "score > 0.95". 
            # If using similarity_search_with_relevance_score, it returns 0-1.
            
            # Let's use similarity_search_with_relevance_scores if possible, or just return the info.
            # The guide says: "HistorySearchTool... score > 0.95". 
            # Inventory search just says "Search Top 3".
            
            content = doc.page_content
            metadata = doc.metadata
            formatted_results.append(f"Content: {content} | Metadata: {metadata}")
            
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
                return f"FOUND: {text}"
            except:
                return f"FOUND: {text}"
        else:
            return "NOT_FOUND"

# Instantiate tools
inventory_search_tool = InventorySearchTool()
history_search_tool = HistorySearchTool()
