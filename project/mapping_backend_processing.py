import fitz
import tempfile
import os
import pymupdf4llm
import pandas as pd
import os
import warnings
import logging 
from openai import OpenAI
import re
import json

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

# Suppress warnings
warnings.filterwarnings("ignore")

def extract_pages_from_pdf(input_pdf_path, page_numbers):
    """
    Extract specified pages from a PDF and return them as a PyMuPDF document.

    Args:
        input_pdf_path (str): Path to the input PDF file.
        page_numbers (list): List of page numbers (1-based index) to extract.

    Returns:
        fitz.Document or None: A PyMuPDF document containing the extracted pages, or None if an error occurs.
    """
    try:
        # Ensure page_numbers is a list
        if not isinstance(page_numbers, list):
            raise ValueError("Page numbers must be provided as a list.")

        if not page_numbers:
            raise ValueError("Page numbers list is empty.")

        # Open the input PDF
        try:
            doc = fitz.open(input_pdf_path)
        except Exception as e:
            raise FileNotFoundError(f"Failed to open the PDF file. Error: {e}")

        # Validate the page range
        valid_pages = [p - 1 for p in page_numbers if 1 <= p <= doc.page_count]
        if not valid_pages:
            raise ValueError("No valid pages to extract. Check the page numbers and try again.")

        # Create a new PDF document for the extracted pages
        new_doc = fitz.open()

        for page_number in valid_pages:
            # Copy each specified page into the new PDF document
            new_doc.insert_pdf(doc, from_page=page_number, to_page=page_number)

        # Close the original document
        doc.close()

        return new_doc

    except FileNotFoundError as fnf_error:
        logger.info(f"File error: {fnf_error}")
        return None
    except ValueError as val_error:
        logger.info(f"Value error: {val_error}")
        return None
    except Exception as general_error:
        logger.info(f"An unexpected error occurred while extract pages from pdf: {general_error}")
        return None


def read_pdf_content_from_document(pdf_document):
    """
    Read the content of a PyMuPDF document and return it as Markdown.

    Args:
        pdf_document (fitz.Document): A PyMuPDF document.

    Returns:
        str: The content of the document in Markdown format, or an error message if an issue occurs.
    """
    temp_path = None

    try:
        # Create a temporary file for the document
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = temp_file.name
            pdf_document.save(temp_path)  # Save the in-memory document to the temp file

        # Use pymupdf4llm to read the content
        pdf_data = pymupdf4llm.to_markdown(temp_path)
        return pdf_data

    except Exception as e:
        logger.info(f"An error occurred while reading the PDF content: {e}")
        return None

    finally:
        # Clean up the temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as cleanup_error:
                logger.info(f"Failed to delete temporary file: {cleanup_error}")


def read_subsheet_from_excel(excel_path, sheet_name):
    """
    Read a specific subsheet from an Excel file.

    Args:
        excel_path (str): Path to the Excel file.
        sheet_name (str): Name of the subsheet to read.

    Returns:
        str or None: The data from the specified subsheet as a string, or None if an error occurs.
    """
    try:
        # Validate input types
        if not isinstance(excel_path, str) or not isinstance(sheet_name, str):
            raise ValueError("Both 'excel_path' and 'sheet_name' must be strings.")
        
        # Attempt to read the specified sheet
        data = pd.read_excel(excel_path, sheet_name=sheet_name)
        return data.to_string()
    
    except FileNotFoundError:
        logger.info(f"File not found: '{excel_path}'. Please check the file path and try again.")
        return None
    
    except ValueError as ve:
        logger.info(f"Value error: {ve}")
        return None

    except Exception as e:
        logger.info(f"An unexpected error occurred while reading the subsheet '{sheet_name}': {e}")
        return None


qwen_api_key = "mjwFUtzq9eusdbBHouQ6pHFxPgnDrMq5"

SYSTEM_PROMPT = '''
You are a meticulous data-processing assistant specializing in aligning financial data from a PDF and Excel into a unified, structured dictionary format for export to Excel. 

Output:
- Strictly ensure all value lists are of equal length.

'''

prompt = """
Task:Your objective is to merge and align financial balance sheet data from two sources: a PDF data and an Excel data.

PDF data : 

{put pdf data here}


Excel data:

{put excel data here}


Step by step instructions:

1. Compare the financial data categories and values between the PDF and Excel sources:
   - Ensure **all categories from the Excel data** are retained, including headers and categories with blank or `None` values for any year.
   - Match and align each financial category across both sources.

2. Handle year-specific data:
   - For years that exist in **both PDF and Excel**:
     - Retain the values from the Excel data **exactly as they are**.
   - For years that exist in the PDF but are **missing in the Excel**:
     - Add those missing year values from the PDF into the output.
   - Use an empty string (`""`) or `null` as a placeholder if a value is missing in both sources.

3. Include missing categories:
   - Every category and header present in the Excel data must appear in the final output, even if **all its year values are blank or `None**.
   - Do not drop any categories or headers, regardless of whether they contain data or not.

4. Output format:
   - Output a dictionary where:
     - First key value pair is of form {"Category": [category names from Excel Data]}
     - And remaining key value pairs are of form: {"FY":<value-list for the categories in order of category names>} where <value-list> follows following rules,
     - If FY present only in Excel Data: {"FY" : [values of FY from the Excel Data]}
     - If FY present only in pdf data: {"FY" : [values of FY from the pdf data]}
     - If FY present in both pdf and Excel Data: {"FY" : [values of FY from the Excel Data]}
   - For a value in the value-list that is found in both Excel Data and pdf data always output a value from Excel Data.
   - If a value in the value-list for a given category cannot be found either in excel or pdf data then put a placeholder "NA" 
   - Ensure the order of the financial categories matches the order in the Excel data.
   - All lists must have the **same length**, ensuring consistency for export into Excel.

5. Output format example (for reference only, do not hard-code this example):

     ``` 
     {
         "Category": [category names from Excel Data],
         "1945": [values for 1945 FY],
         "1950": [values for 1950 FY],
         "1952": [values for 1952 FY],
         ...
     }

     ```

6. STRICTLY ENSURE:
   - **Excel data must take priority for year values that overlap.**
   - Verify that all categories and data are correctly aligned and consistent for export.
   - Ensure **no category or year from the Excel is omitted**
   - Ensure **no year from the pdf is omitted**

Note: 
  - Do not provide explanations, only return the final output dictionary.
  - Ensure that all columns have the **same length** and that the final output is ready for direct export into Excel.

"""

def prepare_prompt(raw_prompt, pdf_data, excel_data):
    """
    Prepares a prompt by replacing placeholders with the provided PDF and Excel data.

    Args:
        raw_prompt (str): The raw prompt string containing placeholders.
        pdf_data (str): The content to replace the '{put pdf data here}' placeholder.
        excel_data (str): The content to replace the '{put excel data here}' placeholder.

    Returns:
        str: The formatted prompt with placeholders replaced, or None if an error occurs.
    """
    try:
        # Validate inputs
        if not isinstance(raw_prompt, str):
            raise ValueError("The 'raw_prompt' must be a string.")
        if not isinstance(pdf_data, str):
            raise ValueError("The 'pdf_data' must be a string.")
        if not isinstance(excel_data, str):
            raise ValueError("The 'excel_data' must be a string.")

        # Replace placeholders in the raw prompt
        prompt_with_inputs = raw_prompt.replace('{put pdf data here}', pdf_data).replace('{put excel data here}', excel_data)
        return prompt_with_inputs

    except ValueError as ve:
        logger.info(f"Input validation error: {ve}")
        return None
    except Exception as e:
        logger.info(f"An unexpected error occurred while preparing the input prompt: {e}")
        return None


def calling_qwen(api_key, system_prompt, user_prompt):
    """
    Generate a chat completion using the specified OpenAI model.

    Parameters:
    - api_key (str): Your DeepInfra API key.
    - system_prompt (str): The system's initial prompt.
    - user_prompt (str): The user's input prompt.

    Returns:
    - str: The response content from the model, or None if an error occurs.
    """
    try:
        # Validate inputs
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("The 'api_key' must be a non-empty string.")
        if not isinstance(system_prompt, str):
            raise ValueError("The 'system_prompt' must be a string.")
        if not isinstance(user_prompt, str):
            raise ValueError("The 'user_prompt' must be a string.")

        # Initialize the OpenAI API with the provided DeepInfra endpoint
        openai = OpenAI(
            api_key=api_key,
            base_url="https://api.deepinfra.com/v1/openai",
        )

        # Make the chat completion request
        chat_completion = openai.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            top_p=0.8
        )

        # Extract and return the response content
        response_content = chat_completion.choices[0].message.content
        logger.info(f'Model respones: {response_content}')
        return response_content

    except ValueError as ve:
        logger.info(f"Input validation error: {ve}")
        return None
    except KeyError as ke:
        logger.info(f"Key error while processing the response: {ke}")
        return None
    except Exception as e:
        logger.info(f"An unexpected error occurred while making a request to Qwen: {e}")
        return None


### have to add error handling
def extract_json_from_the_model_response(jsn_data):
    """
    Extract JSON data from a model prediction.

    Parameters:
    - jsn_data (str): The input string containing JSON data.

    Returns:
    - dict: Parsed JSON data.
    """
    try:
        # Validate input type
        if not isinstance(jsn_data, str):
            raise ValueError("Input data must be a string.")
        
        match = re.search(r"```python\n(.*)\n```", jsn_data, re.DOTALL)
        if match:
            json_data = match.group(1) or match.group(2)
            cleaned_data = json.loads(json_data)

            return cleaned_data
        else:
            logger.info("\n.....................................NO JSON FOUND IN THE MODEL RESPONSE.....................................\n")   
            return {}

    except ValueError as ve:
        logger.info(f"Input validation error: {ve}")
        return {}
    
    except Exception as e:
        logger.info("Unexpected error occurred while extracting JSON data:", e)
        return {}
    

def normalize_and_convert_to_dataframe(cleaned_data):
    """
    Normalizes a dictionary of lists by ensuring all lists have the same length 
    and converts it to a pandas DataFrame.
    
    Args:
        cleaned_data (dict): A dictionary where each key is a column name, 
                             and the values are lists representing column data.
                             
    Returns:
        pd.DataFrame: A DataFrame with normalized column lengths.
    """
    try:
        # Validate input
        if not isinstance(cleaned_data, dict):
            raise ValueError("Input must be a dictionary.")
        if not all(isinstance(values, list) for values in cleaned_data.values()):
            raise ValueError("All values in the dictionary must be lists.")
        
        max_length = max(len(values) for values in cleaned_data.values())

        # Ensure all lists have the same length by appending empty strings where needed
        for key, values in cleaned_data.items():
            if len(values) < max_length:
                logger.info(f"All columns' lengths are not the same for key '{key}'... Adjusting.")
                cleaned_data[key] += [''] * (max_length - len(values))

        # Convert the dictionary to a DataFrame
        df = pd.DataFrame(cleaned_data)
        return df
    
    except ValueError as ve:
        logger.info(f"Value error: {ve}")
        return pd.DataFrame()  # Return an empty DataFrame on error
    
    except Exception as e:
        logger.info(f"An unexpected error occurred: {e}")
        return pd.DataFrame()
    

def process_mapping_task(
    input_excel_path,
    input_pdf_path,
    pages_to_extract,
    excel_sheet_name,
    prompt,
    qwen_api_key,
    SYSTEM_PROMPT
):
    """
    Process the mapping task by extracting pages from a PDF, reading data from an Excel file, 
    and calling the Qwen API for processing.

    Parameters:
        input_excel_path (str): Path to the Excel file.
        input_pdf_path (str): Path to the PDF file.
        pages_to_extract (list): List of pages to extract from the PDF (1-based index).
        excel_sheet_name (str): Name of the sheet to read from the Excel file.
        prompt (str): Initial prompt for Qwen API.
        qwen_api_key (str): API key for the Qwen API.
        SYSTEM_PROMPT (str): System-level prompt for the Qwen API.

    Returns:
        dict: Extracted JSON response from the model.
    """
    try:
        # Validate inputs
        if not isinstance(pages_to_extract, list):
            raise ValueError("The 'pages_to_extract' must be a list.")
        
        # Extract the specified pages
        extracted_pages_doc = extract_pages_from_pdf(input_pdf_path, pages_to_extract)

        if not extracted_pages_doc:
            raise ValueError("Failed to extract pages from the PDF.")

        try:
            # Read the content of the extracted pages
            pdf_input = read_pdf_content_from_document(extracted_pages_doc)

            # Read the specified sheet from the Excel file
            excel_input = read_subsheet_from_excel(input_excel_path, excel_sheet_name)
            if not excel_input:
                raise ValueError("Failed to read the specified sheet from the Excel file.")
            
            # Prepare the prompt with inputs
            prompt_with_inputs = prepare_prompt(prompt, pdf_input, excel_input)

            # Call the Qwen API
            response = calling_qwen(qwen_api_key, SYSTEM_PROMPT, prompt_with_inputs)
            if not response:
                raise ValueError("Failed to get a response from the Qwen.")
            
            # Extract JSON from the model response
            extracted_res = extract_json_from_the_model_response(response)
            if not extracted_res:
                raise ValueError("Failed to extract JSON from the model response.")
            
            df = normalize_and_convert_to_dataframe(extracted_res)

            if df.empty:
                raise ValueError("The resulting DataFrame is empty.")
            
            return df

        finally:
            # Ensure the extracted pages document is closed
            extracted_pages_doc.close()

    except Exception as e:
        logger.info(f"Error during the mapping task: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error
    


def process_financial_statements(pdf_path, excel_path, pages, prompt, qwen_api_key, SYSTEM_PROMPT):
    """
    Process financial statements by extracting relevant pages from the PDF, processing them,
    and saving the results to an Excel file.

    Args:
        pdf_path (str): Path to the PDF file.
        excel_path (str): Path to the Excel file.
        pages (dict): A dictionary mapping financial statement names to lists of page numbers.
        prompt (str): Prompt for the model.
        qwen_api_key (str): API key for Qwen API.
        SYSTEM_PROMPT (str): System-level prompt for the Qwen API.

    Returns:
        str: Path to the output Excel file.
    """
    # Initialize DataFrames for each statement
    income_df = pd.DataFrame()
    balance_sheet_df = pd.DataFrame()
    cash_flow_df = pd.DataFrame()

    # Process each financial statement
    for key, value in pages.items():

        if key == "income":
            key = "INcome Statement"
            if value:
                income_df = process_mapping_task(excel_path, pdf_path, value, key, prompt, qwen_api_key, SYSTEM_PROMPT)
                logger.info('Successfully completed INCOME STATEMENT sheet ------------------------------')
            else:
                logger.info("Provide page numbers for Income Statement.")
        elif key == "balance":
            key = "Balance Sheet"
            if value:
                balance_sheet_df = process_mapping_task(excel_path, pdf_path, value, key, prompt, qwen_api_key, SYSTEM_PROMPT)
                logger.info('Successfully completed BALANCE SHEET sheet ------------------------------')
            else:
                logger.info("Provide page numbers for Balance Sheet.")
        elif key == "cashFlow":
            key = "Cash Flow Statement"
            if value:
                cash_flow_df = process_mapping_task(excel_path, pdf_path, value, key, prompt, qwen_api_key, SYSTEM_PROMPT)
                logger.info('Successfully completed CASH FLOW STATEMENT sheet ------------------------------')
            else:
                logger.info("Provide page numbers for Cash Flow Statement.")

    # Output file path
    output_file = "/home/lenovo/Desktop/personal_projects/MAPPING_TASK/project-bolt-sb1-313mfdpw(1)/project/output_files/final_output4.xlsx"
    
    # Save the DataFrames to Excel
    with pd.ExcelWriter(output_file) as writer:
        income_df.to_excel(writer, sheet_name="INcome Statement", index=False)
        balance_sheet_df.to_excel(writer, sheet_name="Balance Sheet", index=False)
        cash_flow_df.to_excel(writer, sheet_name="Cash Flow Statement", index=False)

    logger.info('Saved processes statements file ..................')

    return output_file


