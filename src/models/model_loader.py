"""
model_loader.py — Cargador del SLM para detección de Botnets mediante LangChain

Responsabilidades:
  1. Proveer la instancia ChatOllama con Qwen2.5 (8-bits).
  2. Proveer el ChatPromptTemplate para inyectar las 15 características en el formato ChatML.
  3. Proveer un health-check de accesibilidad de red.
"""

from pathlib import Path
import requests
from langchain_ollama import OllamaLLM

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "modelos_entrenados"

# Configuración del servidor y modelo
OLLAMA_MODEL_NAME = "qwen2.5_botnet"
OLLAMA_BASE_URL = "http://localhost:11434"

def check_ollama_health() -> bool:
    """Verifica que el servicio Ollama esté activado."""
    try:
        resp = requests.get(OLLAMA_BASE_URL, timeout=5)
        return resp.status_code == 200
    except requests.ConnectionError:
        print("⚠️  Ollama no está corriendo. Inicia el servicio con: ollama serve")
        return False
    except Exception as e:
        print(f"⚠️  Error inesperado verificando Ollama: {e}")
        return False

def get_llm():
    """
    Instancia el modelo local envuelto bajo LangChain.
    Usa el nombre definido al crear el Modelfile (Completado de Texto Puro).
    """
    return OllamaLLM(
        model=OLLAMA_MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1
    )

# La construcción del prompt se trasladó a HumanMessage nativo en nodes.py para evitar sesgos de LangChain
