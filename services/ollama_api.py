import requests
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Hardcoded Ollama endpoint and model
OLLAMA_ENDPOINT = "http://localhost:11434"
OLLAMA_MODEL = "mistral:latest"

def query_ollama(prompt, temperature=0.7, max_tokens=500):
    """
    Send a prompt to the Ollama local API and return the response.
    
    Args:
        prompt (str): The input prompt for the model.
        temperature (float): Controls randomness (0.0–1.0). Default: 0.7.
        max_tokens (int): Maximum tokens in the response. Default: 500.
    
    Returns:
        str: The generated text or an error message.
    """
    try:
        # Set up retry strategy
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("http://", HTTPAdapter(max_retries=retries))
        
        # Prepare the payload
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        # Send POST request to Ollama API
        response = session.post(f"{OLLAMA_ENDPOINT}/api/generate", json=payload, timeout=30)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        return result.get("response", "No response text found")
    
    except requests.exceptions.ConnectionError:
        return "Error: Ollama server is not running or unreachable"
    except requests.exceptions.Timeout:
        return "Error: Request to Ollama timed out after 30 seconds"
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP error occurred: {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred: {str(e)}"