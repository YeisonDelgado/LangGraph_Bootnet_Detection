"""
main.py — Punto de entrada del sistema de detección de botnets.

Importa el grafo compilado de LangGraph y lo ejecuta con un estado
inicial simulado. En producción, el estado vendría de un broker
MQTT/Kafka o un sniffer de red.
"""

from src.graph.workflow import botnet_agent
from src.graph.state import BotnetState

if __name__ == "__main__":
    print("=" * 60)
    print("🖥️  Sistema de Detección de Botnets — LangGraph + SLM Edge")
    print("=" * 60)

    # ── Simulación: vector de features (15 items) para Ataque Mirai ──
    # Valores inflados típicos del dataset N-BaIoT en ataques TCP SYN/UDP
    vector_red = [
        122.12, 105.45, 30.05, 800.88, 120.4,
        90.0, 101.11, 203.5, 45.3, 0.15,
        15.5, 9.2, 5.9, 0.5, 88.8,
    ]

    estado_inicial: BotnetState = {
        "messages": [],
        "network_data": vector_red,
        "source_ip": "192.168.1.105",
        "prediction": "",
        "security_action": "",
        "actions_log": [],
    }

    resultado = botnet_agent.invoke(estado_inicial)

    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    print(f"🔮 Predicción SLM:    {resultado['prediction']}")
    print(f"🤖 Acción Defensiva:  {resultado['security_action']}")
    print(f"📋 Tools ejecutadas:  {len(resultado['actions_log'])}")
    for i, action in enumerate(resultado["actions_log"], 1):
        print(f"   {i}. {action['tool']} → {action['result']['status']}")
    print("=" * 60)
