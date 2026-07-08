import os
from ollama import chat, Client

# 1. Define your drawing file path and choice of model
IMAGE_PATH = "./data/shrub_ai/ocr/test3.png" 
MODEL_NAME = "qwen2.5vl:7b"  # or 'llama3.2-vision' / 'glm-ocr'
MINIKUBE_OLLAMA_URL = "http://localhost:11434"
# Quick safety check
if not os.path.exists(IMAGE_PATH):
    raise FileNotFoundError(f"Could not find the sketch image at: {IMAGE_PATH}")

# 2. Craft a structured prompt optimized for drawing annotations
OWL_PROMPT_INSTRUCTION = (
    "Perform a highly accurate architectural OCR on this drawing sketch. "
    "Include connections between shapes, and the direction of the connection, and containment relations (shapes in shapes). Include handwritten texts inside boxes and near lines."
    "Present the extracted data cleanly as OWL DL 2.0 in the format RDF turtle file according to the 1.2 specification (RDF STAR)." \
    "Make sure that all used prefixes are present in the output."
)
RDF_START_PROMPT_INSTRUCTION = (
    "Perform a highly accurate architectural OCR on this drawing sketch. "
    "Include connections between shapes, and the direction of the connection, and containment relations (shapes in shapes). Include handwritten texts inside boxes and near lines."
    "Present the extracted data cleanly in a RDF turtle file according to the 1.2 specification (RDF STAR)." \
    "Make sure that all used prefixes are present in the output."
)


prompt_instructions = RDF_START_PROMPT_INSTRUCTION

print(f"🔄 Processing image with local model '{MODEL_NAME}'...")

try:
    client = Client(host=MINIKUBE_OLLAMA_URL)
    
    # 3. Call the Ollama Python client
    response = client.chat(
        model=MODEL_NAME,
        messages=[
            {
                'role': 'user',
                'content': prompt_instructions,
                'images': [IMAGE_PATH]  # Pass the file path directly in the list
            }
        ],
        options={
            'temperature': 0.1  # Keep temperature low for deterministic, accurate OCR text
        }
    )

    # 4. Print the extracted OCR result
    print("\n--- Extracted Sketch Text ---")
    print(response.message.content)

except Exception as e:
    print(f" An error occurred during processing: {e}")