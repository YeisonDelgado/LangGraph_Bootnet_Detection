import os
from typing import TypedDict, Annotated, Literal
from asgiref.sync import sync_to_async
import torch
import numpy as np

# Dependencias LangGraph / LangChain
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

# Importar modelo entrenado con LoRA (ejemplo base)
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from peft import PeftModel

class BotnetState(TypedDict):
    """
    Estado compartido que LangGraph utiliza en cada nodo.
    - messages: El historial de chat (si fuera interactivo).
    - network_data: La tupla o array de valores de red del Edge node.
    - prediction: El tipo de amenaza clasificada.
    - security_action: La acción defensiva a tomar basada en la predicción.
    """
    messages: list
    network_data: list
    prediction: str
    security_action: str

# Configuración del modelo SLM
# NOTA: Cambiar `base_model_path` por el path base del SLM (ej. HuggingFaceTB/SmolLM-360M-Instruct)
# y `lora_adapter_path` al path donde se guardaron los pesos LoRA entrenados en el notebook.
base_model_path = "distilroberta-base" # REEMPLAZAR con el modelo ganador del benchmark
lora_adapter_path = "./modelos_entrenados/mi_modelo_lora" # REEMPLAZAR con tu carpeta

def load_slm_model():
    """ 
    Carga el modelo principal e inyecta los adaptadores LoRA entrenados 
    """
    try:
        model = AutoModelForSequenceClassification.from_pretrained(base_model_path, num_labels=3)
        # model = PeftModel.from_pretrained(model, lora_adapter_path)
        print("✅ Modelo cargado correctamente.")
        return model
    except Exception as e:
        print(f"⚠️ Advertencia, configuración de modelo no encontrada: {e}")
        return None

# Instancia del modelo global
detector_model = load_slm_model()

# ==========================================
# DEFINICION DE NODOS DE LANGGRAPH CARGADOS CON SLM
# ==========================================

def node_extract_features(state: BotnetState):
    """ Este nodo simula extraer/validar el array de datos de red """
    print("📡 Pasando por [Extractor de Red]...")
    return state

def node_predict_botnet(state: BotnetState):
    """ 
    Este nodo corre la inferencia sobre el SLM con LoRA 
    """
    print("🧠 Pasando por [Inferencia SLM]...")
    data = state.get("network_data", [])
    
    # Check si el modelo cargó
    if detector_model is None or not data:
        state["prediction"] = "Error_Modelo_o_Datos"
        return state

    # Simular la inferencia en PyTorch
    # features_tensor = torch.tensor([data]).float()
    # with torch.no_grad():
    #     logits = detector_model(features_tensor).logits
    #     pred = torch.argmax(logits, dim=1).item()
    
    # Mapeo de predicciones desde el entrenamiento (0: Normal, 1: Mirai, 2: Gafgyt)
    prediccion_demo = "Ataque_Mirai"  # Aquí pondrías la salida real
    state["prediction"] = prediccion_demo
    
    return state

def node_firewall_rule(state: BotnetState):
    """
    Toma decisiones basadas en la clasificación
    """
    print("🛡️ Pasando por [Orquestador de Seguridad]...")
    pred = state.get("prediction", "Desconocido")
    
    if pred == "Ataque_Mirai" or pred == "Ataque_Gafgyt":
        state["security_action"] = f"BLOQUEAR IP - Patrón detectado: {pred}"
    else:
        state["security_action"] = "Permitir Tráfico"
        
    return state

# ==========================================
# CREANDO EL GRAFO DE LANGGRAPH
# ==========================================

builder = StateGraph(BotnetState)

builder.add_node("extractor", node_extract_features)
builder.add_node("detector", node_predict_botnet)
builder.add_node("firewall", node_firewall_rule)

builder.add_edge(START, "extractor")
builder.add_edge("extractor", "detector")
builder.add_edge("detector", "firewall")
builder.add_edge("firewall", END)

botnet_agent = builder.compile()

if __name__ == "__main__":
    print("-" * 50)
    print("🖥️ Iniciando Prueba de LangGraph con el Modelo SLM Edge")
    print("-" * 50)
    
    # Simulamos el vector de características reducido (ej. 15 top features de red)
    vector_red = [0.12, 1.45, 0.05, 0.88, 120.4, 0.0, 1.11, 23.5, 4.3, 0.11, 0.5, 0.2, 0.9, 0.1, 8.8]
    
    estado_inicial: BotnetState = {
        "messages": [],
        "network_data": vector_red,
        "prediction": "",
        "security_action": ""
    }
    
    resultado = botnet_agent.invoke(estado_inicial)
    
    print("\n✅ Flujo completado.")
    print("🔮 Predicción SLM:", resultado["prediction"])
    print("🤖 Acción de Defensa:", resultado["security_action"])
