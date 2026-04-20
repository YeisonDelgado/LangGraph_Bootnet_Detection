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

    # ── Casos de Prueba ──
    # 1. Tráfico Normal (valores pequeños, fluctuaciones lentas)
    vector_normal = [
        0.01, 1.05, 0.02, 0.98, 14.4,
        0.0, 1.01, 3.5, 0.3, 0.01,
        0.5, 0.2, 0.9, 0.1, 0.8,
    ]

    # 2. Ataque Mirai (valores inflados, inundación de paquetes TCP/UDP)
    vector_mirai = [
        1202.12, 1202.12, 0.45, 30.05, 800.88, 120.4,
        90.0, 101.11, 203.5, 45.3, 0.15,
        15.5, 9.2, 5.9, 0.5, 118.8,
    ]

    escenarios = [
        {"nombre": "Tráfico Normal", "ip": "192.168.1.10", "datos": vector_normal},
        {"nombre": "Ataque Mirai", "ip": "192.168.1.105", "datos": vector_mirai},
    ]

    for esc in escenarios:
        print(f"\n🚀 EJECUTANDO SIMULACIÓN: {esc['nombre'].upper()}")
        print("-" * 60)
        
        estado_inicial: BotnetState = {
            "messages": [],
            "network_data": esc["datos"],
            "source_ip": esc["ip"],
            "prediction": "",
            "security_action": "",
            "actions_log": [],
        }

        resultado = botnet_agent.invoke(estado_inicial)

        print("\n" + "=" * 60)
        print(f"📊 RESULTADO FINAL - {esc['nombre']}")
        print("=" * 60)
        print(f"🔮 Predicción SLM:    {resultado['prediction']}")
        print(f"🤖 Acción Defensiva:  {resultado['security_action']}")
        print(f"📋 Tools ejecutadas:  {len(resultado['actions_log'])}")
        for i, action in enumerate(resultado["actions_log"], 1):
            print(f"   {i}. {action['tool']} → {action['result']['status']}")
        print("=" * 60)
