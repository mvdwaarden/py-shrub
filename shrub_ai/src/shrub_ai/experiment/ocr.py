import datetime
import os, time
from ollama import chat, Client

# 1. Define your drawing file path and choice of model
TEST_NR = 5
IMAGE_PATH = f"./data/shrub_ai/ocr/test{TEST_NR}.png" 
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
    "Make sure that all used prefixes are present in the header."
)

RDF_STAR_PROMPT_INSTRUCTION = (
    "Perform a highly accurate architectural OCR on this drawing sketch. "
    "Include connections between shapes, and the direction of the connection, and containment relations (shapes in shapes). Include handwritten texts inside boxes and near lines."
    "Present the extracted data cleanly in a RDF turtle file according to the 1.2 specification (RDF STAR)." \
    "Make sure that all used prefixes are present in the header."
)

RDF_PROMPT_INSTRUCTION = (
    "Perform a highly accurate architectural OCR on this drawing sketch. "
    "Include connections between shapes, and the direction of the connection, and containment relations (shapes in shapes). Include handwritten texts inside boxes and near lines."
    "Present the extracted data cleanly in a RDF compliant turtle file" \
    "Make sure that all used prefixes are present in the header."
)

UPDATED_GEMINI_INSTRUCTION = """
    Perform a highly accurate architectural OCR on this drawing sketch.
    Instructions for RDF representation:
    1) Identify entities: Extract all shapes (with their labels) and containment relations (e.g., arch:contains).
    2) Model connections semantically: Instead of using RDF-star quoted triples (<< s p o >>) to describe connection types, use a property hierarchy.
    3) Define a base property arch:connectsTo.
    4) Create sub-properties for specific connection types (e.g., arch:hasArrow, arch:hasSolidLine, arch:hasProximity).
    5) Use these sub-properties to represent the edges between nodes directly.
    Format: Present the data in a clean RDF Turtle file. Include all necessary prefixes in the header.
    Goal: Minimize redundancy by avoiding unnecessary metadata triples; rely on the schema hierarchy to define relationship characteristics."""

PLANT_UML_INSTRUCTION = """
    Perform a highly accurate architectural OCR on this drawing sketch.
    1) Identify entities: Extract all shapes (with their labels) and containment relations.
    2) Identify other relations between the entities based on lines between the shapes and text near the line.
    3) The entities are the nodes and the relations are the vertices.
    4) Identity which plant UML diagram is the most appropriate for the extracted data (class, sequence, use case, component, state, activity, object, deployment, timing, communication).
    5) Present the extracted data cleanly as a Plant UML diagram in the appropriate format   
"""

prompt_instructions = PLANT_UML_INSTRUCTION  # Choose the appropriate prompt based on your needs

print(f"🔄 Processing image with local model '{MODEL_NAME}'...")
start_time = datetime.datetime.now()
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
    total_time = datetime.datetime.now() - start_time
    print(f"\n--- Processing Time ---")
    print(f"Total time taken: {total_time:.2f}")
    # 4. Print the extracted OCR result
    print("\n--- Extracted Sketch Text ---")
    print(response.message.content)
    now = datetime.datetime.now()
    with open(f"./data/shrub_ai/ocr/{now.strftime('%y%m%d.%H%M%S')}.{TEST_NR}.txt", "w") as f:
        f.write(response.message.content)


except Exception as e:
    print(f" An error occurred during processing: {e}")