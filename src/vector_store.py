import os
import glob
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from src.config import API_KEY, API_BASE, EMBEDDING_MODEL
from src.utils import load_data

# Initialize Embeddings
embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    openai_api_key=API_KEY,
    openai_api_base=API_BASE,
    chunk_size=50 # SiliconFlow limit is 64
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
    
    # Check if inventory collection already exists and is populated
    try:
        test_inv = Chroma(
            collection_name="inventory",
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIR
        )
        if test_inv.get()['ids']:
            print("Inventory Knowledge Base already exists. Skipping build.")
        else:
            raise ValueError("Collection empty")
    except Exception:
        # Rebuild if not exists or empty
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
    # Check if history collection already exists and is populated
    try:
        test_hist = Chroma(
            collection_name="history",
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIR
        )
        if test_hist.get()['ids']:
            print("History Knowledge Base already exists. Skipping build.")
            return # Exit function if both are good
        else:
             raise ValueError("Collection empty")
    except Exception:
        pass # Continue to build

    # Look in History_BOM directory for Excel files
    history_files = glob.glob("History_BOM/*.xls") + glob.glob("History_BOM/*.xlsx")
    if not history_files:
        print("No history BOMs found in History_BOM/. Skipping history base.")
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
