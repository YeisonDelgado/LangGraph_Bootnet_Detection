"""
model_loader.py — Cargador del SLM para detección de Botnets mediante LangChain

Responsabilidades:
  1. Proveer la instancia ChatOllama con Qwen2.5 (8-bits).
  2. Proveer el ChatPromptTemplate para inyectar las 15 características en el formato ChatML.
  3. Proveer un health-check de accesibilidad de red.
"""

from pathlib import Path
import requests
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

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
    Usa el nombre definido al crear el Modelfile.
    """
    return ChatOllama(
        model=OLLAMA_MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1
    )

def get_botnet_prompt_template():
    """
    Construye y devuelve un ChatPromptTemplate mapeando exactamente 15 características.
    Nota: El mensaje de sistema ya está inyectado directamente desde el Modelfile. 
    Este template será el prompt de 'user'.
    """
    template = (
        "Analiza el siguiente vector de red y determina la clase:\n\n"
        "- F01 (MI_dir_L5_weight): {f01}\n"
        "- F02 (MI_dir_L5_mean): {f02}\n"
        "- F03 (MI_dir_L5_variance): {f03}\n"
        "- F04 (H_L5_weight): {f04}\n"
        "- F05 (H_L5_mean): {f05}\n"
        "- F06 (H_L5_variance): {f06}\n"
        "- F07 (HH_L5_weight): {f07}\n"
        "- F08 (HH_L5_mean): {f08}\n"
        "- F09 (HH_L5_std): {f09}\n"
        "- F10 (HH_L5_magnitude): {f10}\n"
        "- F11 (HH_L5_radius): {f11}\n"
        "- F12 (HH_L5_covariance): {f12}\n"
        "- F13 (HH_L5_pcc): {f13}\n"
        "- F14 (HH_L0.01_weight): {f14}\n"
        "- F15 (HH_L0.01_std): {f15}\n"
    )
    
    return ChatPromptTemplate.from_messages([
        ("user", template)
    ])
