from typing import TypedDict

class BotnetState(TypedDict):
    """
    Estado compartido que LangGraph utiliza en cada nodo.

    Campos:
      - messages:        Historial de chat (si fuera interactivo).
      - network_data:    Vector de features numéricas del tráfico de red.
      - source_ip:       Dirección IP origen del tráfico analizado.
      - prediction:      Etiqueta de clasificación del SLM (Normal, Ataque_Mirai, etc.).
      - security_action: Descripción de la acción defensiva tomada.
      - actions_log:     Lista de resultados de las tools ejecutadas (block, siem, etc.).
    """
    messages: list
    network_data: list
    source_ip: str
    prediction: str
    security_action: str
    actions_log: list
