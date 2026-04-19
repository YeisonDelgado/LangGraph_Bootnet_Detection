"""
nodes.py — Nodos del grafo LangGraph para detección de botnets.

Cada función recibe y retorna un BotnetState, mutando las claves
relevantes durante su ejecución.

Pipeline:  Extractor → Detector (SLM vía Ollama) → Firewall (Tools)
"""

from src.graph.state import BotnetState
from src.models.model_loader import (
    check_ollama_health,
    get_llm,
    get_botnet_prompt_template
)
from src.tools.firewall_actions import block_ip_address, log_to_siem

# ──────────────────────────────────────────────
# Etiquetas válidas que el modelo debe retornar
# ──────────────────────────────────────────────
VALID_LABELS = {"Normal", "Mirai", "Gafgyt"}
ATTACK_LABELS = {"Mirai", "Gafgyt"}
ERROR_LABELS = {"Error_Inferencia", "Error_Modelo_o_Datos", "Desconocido"}


def _parse_model_response(raw_text: str) -> str:
    """
    Extrae la etiqueta de clasificación de la respuesta cruda de LangChain.
    """
    cleaned = raw_text.strip()
    for label in VALID_LABELS:
        if label.lower() in cleaned.lower():
            return label
    return "Desconocido"


# ==========================================
# NODO 1 — EXTRACTOR DE FEATURES
# ==========================================
def node_extract_features(state: BotnetState) -> BotnetState:
    """
    Valida y pre-procesa el vector de datos de red.
    En producción aquí se conectaría un sniffer o un broker MQTT/Kafka.
    """
    print("📡 Pasando por [Extractor de Red]...")

    data = state.get("network_data", [])
    if not data:
        print("   ⚠️  No se recibieron datos de red.")
    else:
        print(f"   ✔ Vector recibido con {len(data)} features.")

    return state


# ==========================================
# NODO 2 — INFERENCIA SLM VÍA OLLAMA
# ==========================================
def node_predict_botnet(state: BotnetState) -> BotnetState:
    """
    Invoca al SLM (Qwen2.5 GGUF) usando LangChain (ChatOllama).
    """
    print("🧠 Pasando por [Inferencia SLM]...")

    data = state.get("network_data", [])

    if len(data) < 15:
        print(f"   ⚠️  Faltan datos de red (Recibidos {len(data)}, esperados 15).")
        state["prediction"] = "Error_Modelo_o_Datos"
        return state

    if not check_ollama_health():
        state["prediction"] = "Error_Inferencia"
        return state

    llm = get_llm()
    prompt_template = get_botnet_prompt_template()
    chain = prompt_template | llm

    # Preparar el payload de kwargs (f01 a f15)
    features_dict = {f"f{str(i+1).zfill(2)}": f"{val:.4f}" for i, val in enumerate(data[:15])}

    print("   📝 Invocando el SLM vía LangChain (ChatOllama)...")

    try:
        response_msg = chain.invoke(features_dict)
        raw_output = response_msg.content
        prediction = _parse_model_response(raw_output)

        print(f"   ✔ Respuesta cruda del SLM: '{raw_output.strip()}'")
        print(f"   ✔ Etiqueta parseada: {prediction}")

        state["prediction"] = prediction

    except Exception as exc:
        print(f"   ❌ Error inesperado durante la inferencia en LangChain: {exc}")
        state["prediction"] = "Error_Inferencia"

    return state


# ==========================================
# NODO 3 — ORQUESTADOR DE SEGURIDAD / FIREWALL
# ==========================================
def node_firewall_rule(state: BotnetState) -> BotnetState:
    """
    Toma decisiones defensivas basadas en la clasificación del SLM
    e invoca las Tools de seguridad correspondientes.

    Matriz de decisión:
      ┌────────────────────┬──────────────┬──────────────┐
      │ Clasificación      │ block_ip?    │ log_to_siem? │
      ├────────────────────┼──────────────┼──────────────┤
      │ Ataque_Mirai       │ ✅ SÍ        │ ✅ SÍ (HIGH) │
      │ Ataque_Gafgyt      │ ✅ SÍ        │ ✅ SÍ (HIGH) │
      │ Error_Inferencia   │ ❌ NO        │ ✅ SÍ (MED)  │
      │ Desconocido        │ ❌ NO        │ ✅ SÍ (MED)  │
      │ Normal             │ ❌ NO        │ ✅ SÍ (INFO) │
      └────────────────────┴──────────────┴──────────────┘
    """
    print("🛡️ Pasando por [Orquestador de Seguridad]...")

    pred = state.get("prediction", "Desconocido")
    source_ip = state.get("source_ip", "0.0.0.0")
    network_data = state.get("network_data", [])
    actions_log = state.get("actions_log", [])

    # ── CASO 1: Ataque confirmado → Bloquear + Registrar ──
    if pred in ATTACK_LABELS:
        state["security_action"] = f"🔴 BLOQUEAR IP — Patrón detectado: {pred}"
        print(f"   🔴 Amenaza confirmada: {pred} desde {source_ip}")

        # Tool 1: Bloquear IP
        block_result = block_ip_address(ip=source_ip)
        actions_log.append({"tool": "block_ip_address", "result": block_result})
        print(f"   🔒 IP {source_ip} → {block_result['status']}")

        # Tool 2: Registrar en SIEM
        siem_result = log_to_siem(alert_data={
            "threat_type": pred,
            "source_ip": source_ip,
            "action_taken": "BLOCK",
            "network_features": network_data,
            "prediction_raw": pred,
        })
        actions_log.append({"tool": "log_to_siem", "result": siem_result})

    # ── CASO 2: Error de clasificación → Alerta + Registrar sin bloquear ──
    elif pred in ERROR_LABELS:
        state["security_action"] = (
            f"🟡 ALERTA — Clasificación no concluyente: {pred}. "
            f"Requiere revisión manual."
        )
        print(f"   🟡 Clasificación ambigua: {pred}. Registrando alerta...")

        siem_result = log_to_siem(alert_data={
            "threat_type": pred,
            "source_ip": source_ip,
            "action_taken": "ALERT",
            "network_features": network_data,
            "prediction_raw": pred,
        })
        actions_log.append({"tool": "log_to_siem", "result": siem_result})

    # ── CASO 3: Tráfico normal → Permitir + Log informativo ──
    else:
        state["security_action"] = "🟢 Permitir Tráfico — Sin amenaza detectada."
        print(f"   🟢 Tráfico normal desde {source_ip}.")

        siem_result = log_to_siem(alert_data={
            "threat_type": "Normal",
            "source_ip": source_ip,
            "action_taken": "ALLOW",
            "network_features": network_data,
            "prediction_raw": pred,
        })
        actions_log.append({"tool": "log_to_siem", "result": siem_result})

    state["actions_log"] = actions_log
    return state
