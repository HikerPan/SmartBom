import os
import pandas as pd
from crewai import Task, Crew
from src.vector_store import init_knowledge_bases
from src.utils import load_data, clean_footprint, clean_value
from src.agents import bom_matcher_agent

def main():
    # 1. Initialize Knowledge Bases
    init_knowledge_bases()
    
    # 2. Load Raw BOM
    raw_bom_path = "data/raw_bom.csv"
    if not os.path.exists(raw_bom_path):
        print(f"Error: {raw_bom_path} not found.")
        return
        
    print(f"Loading raw BOM from {raw_bom_path}...")
    df_raw = load_data(raw_bom_path)
    
    # 3. Prepare Output DataFrame
    template_path = "data/bom_template.xlsx"
    if os.path.exists(template_path):
        print(f"Loading template from {template_path}...")
        df_out = load_data(template_path)
        # Ensure we have enough rows or append
        # Actually, usually we want to fill in the template matching the raw rows.
        # For simplicity, let's just create a new DF or copy raw and add 'Matched_Code'
        # The guide says: "将 [原始位号, 原始数量, 匹配到的存货编码] 写入对应列"
        # Let's assume we build a result list and create a new DF or update template.
    else:
        print("Template not found, creating new DataFrame.")
        df_out = pd.DataFrame(columns=["Designator", "Quantity", "Matched_Code"])

    results = []
    
    # 4. Processing Loop
    print("Starting processing loop...")

    # --- Define Agent/Task/Crew OUTSIDE the loop ---
    task_description = """
    Find the ERP inventory code for the following component:
    Raw Input: {query}
    
    Details:
    - Value/Comment: {comment} (Cleaned: {clean_val})
    - Footprint: {footprint} (Cleaned: {clean_fp})
    - Description: {description}
    """
    
    task = Task(
        description=task_description,
        expected_output="The ERP Inventory Code (e.g., 10023456) or 'MANUAL_CHECK'",
        agent=bom_matcher_agent
    )
    
    crew = Crew(
        agents=[bom_matcher_agent],
        tasks=[task],
        verbose=False 
    )

    for index, row in df_raw.iterrows():
        # Development limit
        # Development limit removed
        # if index >= 5:
        #     print("Reached development limit (5 rows). Stopping.")
        #     break
            
        # Extract fields (Adjust column names based on actual CSV)
        comment = str(row.get('Comment', ''))
        footprint = str(row.get('Footprint', ''))
        description = str(row.get('Description', ''))
        designator = str(row.get('Designator', ''))
        quantity = str(row.get('Quantity', ''))
        
        # Clean data
        clean_fp = clean_footprint(footprint)
        clean_val = clean_value(comment) 
        
        # Construct structured query for the tool
        query = f"Value:{clean_val}|Footprint:{clean_fp}"
        print(f"\n--- Processing Row {index + 1}: {query} ---")
        
        # Prepare inputs for the task
        inputs = {
            'query': query,
            'comment': comment,
            'clean_val': clean_val,
            'footprint': footprint,
            'clean_fp': clean_fp,
            'description': description
        }
        
        # Execute
        try:
            result = crew.kickoff(inputs=inputs)
            # result is usually a string or TaskOutput
            matched_code = str(result).strip()
            print(f"Result: {matched_code}")
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            matched_code = "ERROR"
            
        results.append({
            "Designator": designator,
            "Quantity": quantity,
            "Matched_Code": matched_code,
            "Original_Row": index
        })

    # 5. Save Results
    output_path = "data/Final_BOM.xlsx"
    print(f"Saving results to {output_path}...")
    
    df_results = pd.DataFrame(results)
    
    # If template existed, we might want to merge, but for now just save what we got
    # or append to template columns if they match.
    # Let's just save the results DF.
    df_results.to_excel(output_path, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
