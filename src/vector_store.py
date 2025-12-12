import os
import glob
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from src.config import API_KEY, API_BASE
from src.utils import load_data

# Initialize Embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=API_KEY,
    openai_api_base=API_BASE
)

# Persistent directory for Chroma
CHROMA_DB_DIR = "chroma_db"

def init_knowledge_bases():
    """
    Initialize or update the two knowledge bases: Inventory and History.
    """
    print("Initializing Knowledge Bases...")
    
    # --- 1. Build Inventory Knowledge Base ---
    inventory_path = "data/inventory.xlsx"
    if os.path.exists(inventory_path):
        print(f"Loading inventory from {inventory_path}...")
        df_inv = load_data(inventory_path)
        
        documents = []
        for _, row in df_inv.iterrows():
            # Construct text content
            text = f"名称: {row.get('存货名称', '')}, 规格: {row.get('规格型号', '')}, 供应商: {row.get('主要供货单位名称', '')}"
            
            # Construct metadata
            metadata = {
                "code": str(row.get('存货编码', '')),
                "spec": str(row.get('规格型号', ''))
            }
            
            documents.append(Document(page_content=text, metadata=metadata))
            
        if documents:
            print(f"Adding {len(documents)} items to Inventory Vector Store...")
            Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                collection_name="inventory",
                persist_directory=CHROMA_DB_DIR
            )
        else:
            print("Warning: Inventory file is empty or invalid.")
    else:
        print(f"Warning: Inventory file not found at {inventory_path}")

    # --- 2. Build History Knowledge Base ---
    history_files = glob.glob("data/history_boms/*.csv")
    if not history_files:
        print("No history BOMs found in data/history_boms/. Skipping history base.")
    else:
        print(f"Found {len(history_files)} history BOM files.")
        documents = []
        for file_path in history_files:
            try:
                df_hist = load_data(file_path)
                for _, row in df_hist.iterrows():
                    # Assuming history files have columns like 'Comment', 'Footprint', 'Matched_Code'
                    # Adjust column names if necessary based on actual history file structure
                    comment = row.get('Comment', '')
                    footprint = row.get('Footprint', '')
                    matched_code = row.get('Matched_Code', '')
                    
                    if matched_code:
                        text = f"原始输入: {comment} {footprint} => 最终编码: {matched_code}"
                        documents.append(Document(page_content=text, metadata={"source": file_path}))
            except Exception as e:
                print(f"Error reading history file {file_path}: {e}")
                
        if documents:
            print(f"Adding {len(documents)} items to History Vector Store...")
            Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                collection_name="history",
                persist_directory=CHROMA_DB_DIR
            )

def get_inventory_retriever(k=3):
    """Get retriever for inventory knowledge base."""
    vectorstore = Chroma(
        collection_name="inventory",
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    return vectorstore.as_retriever(search_kwargs={"k": k})

def get_history_retriever(k=1):
    """Get retriever for history knowledge base."""
    vectorstore = Chroma(
        collection_name="history",
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    return vectorstore.as_retriever(search_kwargs={"k": k})
