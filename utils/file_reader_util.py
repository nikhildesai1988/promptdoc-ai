import os
import pypdf

def process_file(file_input):
    """
    Process uploaded file (PDF or TXT) and extract text content.
    
    :param file_input: Gradio file upload object (has .name attribute with file path)
    :return: Extracted text content as string
    """
    if not file_input:
        return "No file uploaded."
    
    file_path = file_input.name
    
    # Check if file exists
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    
    # Process based on file extension
    if file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    
    elif file_path.endswith('.pdf'):
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = pypdf.PdfReader(f)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
            return content
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    else:
        return "Unsupported file format. Please upload a PDF or TXT file."