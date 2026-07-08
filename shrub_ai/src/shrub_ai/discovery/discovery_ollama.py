#!/usr/bin/env python3

import urllib.request
import urllib.error
import json
import os
import sys

def get_ollama_host():
    """Determine the Ollama host URL, respecting the OLLAMA_HOST environment variable."""
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    # Ensure the host has a scheme
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
    return host

def fetch_json(url):
    """Helper function to perform a GET request and parse the JSON response."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"❌ Could not connect to Ollama.")
        print(f"   Ensure Ollama is running and accessible at {url.rsplit('/', 2)[0]}")
        print(f"   Error Details: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An error occurred while fetching data: {e}")
        sys.exit(1)

def main():
    base_url = get_ollama_host()
    print(f"Initializing Ollama Discovery on {base_url}...\n")

    # --- 1. VERSION INFO ---
    print("="*40)
    print("OLLAMA SYSTEM INFO")
    print("="*40)
    version_data = fetch_json(f"{base_url}/api/version")
    print(f"Ollama Version : {version_data.get('version', 'Unknown')}")

    # --- 2. INSTALLED MODELS ---
    print("\n" + "="*40)
    print("INSTALLED MODELS")
    print("="*40)
    tags_data = fetch_json(f"{base_url}/api/tags")
    models = tags_data.get("models", [])

    if not models:
        print("No models currently installed. You can pull one using 'ollama pull <model_name>'.")
    else:
        print(f"Total Models Found: {len(models)}\n")
        
        # Sort models alphabetically by name
        models = sorted(models, key=lambda x: x.get('name', ''))
        
        for model in models:
            name = model.get("name", "Unknown")
            size_bytes = model.get("size", 0)
            size_gb = size_bytes / (1024 ** 3)
            
            details = model.get("details", {})
            family = details.get("family", "Unknown")
            param_size = details.get("parameter_size", "Unknown")
            quant_level = details.get("quantization_level", "Unknown")
            format_type = details.get("format", "Unknown")
            
            print(f"- Model Name   : {name}")
            print(f"  Size         : {size_gb:.2f} GB")
            print(f"  Architecture : {family} ({param_size})")
            print(f"  Quantization : {quant_level} ({format_type})\n")

    # --- 3. RUNNING MODELS (If Supported) ---
    print("="*40)
    print("CURRENTLY RUNNING MODELS")
    print("="*40)
    try:
        ps_data = fetch_json(f"{base_url}/api/ps")
        running_models = ps_data.get("models", [])
        
        if not running_models:
            print("No models are currently loaded in memory.")
        else:
            for rm in running_models:
                name = rm.get("name", "Unknown")
                size_gb = rm.get("size", 0) / (1024 ** 3)
                print(f"- {name} (Consuming ~{size_gb:.2f} GB in memory)")
    except SystemExit:
        # Ignore exits from fetch_json if the /api/ps endpoint fails, 
        # as older versions of Ollama might not support it.
        pass

    print("\nDiscovery complete.")

if __name__ == '__main__':
    main()