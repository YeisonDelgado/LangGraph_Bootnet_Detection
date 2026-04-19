"""
firewall_actions.py — Herramientas defensivas para el agente de detección de botnets.

Provee dos tools que el nodo Firewall puede invocar:
  1. block_ip_address  → Simula bloqueo de IP vía iptables/ufw (o SSH remoto).
  2. log_to_siem       → Registra el evento de seguridad en formato JSON (SIEM-ready).

Arquitectura:
  - Modo SIMULACIÓN (por defecto): imprime las acciones sin ejecutarlas.
  - Modo PRODUCCIÓN: descomentar las secciones marcadas con [PROD] para
    ejecutar comandos reales vía subprocess o paramiko.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SIEM_LOG_DIR = PROJECT_ROOT / "data" / "siem_logs"
SIEM_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logger dedicado para auditoría de acciones de seguridad
logger = logging.getLogger("firewall_actions")
logger.setLevel(logging.INFO)

# Handler de archivo rotativo para persistencia local
_log_file = SIEM_LOG_DIR / "firewall_events.log"
if not logger.handlers:
    _fh = logging.FileHandler(_log_file, encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(_fh)
    # También imprimir en consola
    _ch = logging.StreamHandler()
    _ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(_ch)


# ==========================================
# TOOL 1 — BLOQUEO DE IP
# ==========================================
def block_ip_address(ip: str) -> dict:
    """
    Simula el bloqueo de una dirección IP sospechosa en el firewall.

    En modo simulación imprime el comando que se ejecutaría.
    En producción, puede usar:
      - subprocess para iptables/ufw local.
      - paramiko para ejecución SSH remota en un gateway.

    Args:
        ip: Dirección IPv4/IPv6 a bloquear.

    Returns:
        dict con el resultado de la operación.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Comando que se ejecutaría en producción
    iptables_cmd = f"sudo iptables -A INPUT -s {ip} -j DROP"
    ufw_cmd = f"sudo ufw deny from {ip}"

    # ── SIMULACIÓN ──
    logger.info(f"[SIMULACIÓN] Bloqueando IP: {ip}")
    logger.info(f"  → Comando iptables: {iptables_cmd}")
    logger.info(f"  → Comando ufw:      {ufw_cmd}")

    # ── [PROD] Ejecución real con subprocess ──
    # import subprocess
    # try:
    #     result = subprocess.run(
    #         ["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
    #         capture_output=True, text=True, timeout=10
    #     )
    #     if result.returncode != 0:
    #         logger.error(f"iptables falló: {result.stderr}")
    #         return {"status": "error", "ip": ip, "detail": result.stderr}
    # except subprocess.TimeoutExpired:
    #     logger.error(f"Timeout ejecutando iptables para {ip}")
    #     return {"status": "error", "ip": ip, "detail": "timeout"}

    # ── [PROD] Ejecución remota con paramiko ──
    # import paramiko
    # ssh = paramiko.SSHClient()
    # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect("192.168.1.1", username="admin", key_filename="/path/to/key")
    # stdin, stdout, stderr = ssh.exec_command(iptables_cmd)
    # ssh.close()

    return {
        "status": "blocked",
        "ip": ip,
        "command": iptables_cmd,
        "timestamp": timestamp,
        "mode": "simulation",
    }


# ==========================================
# TOOL 2 — LOGGING A SIEM
# ==========================================
def log_to_siem(alert_data: dict) -> dict:
    """
    Registra un evento de seguridad en formato JSON compatible con SIEM
    (Splunk, Elastic SIEM, Wazuh, etc.).

    Persiste el log en dos destinos:
      1. Archivo .jsonl rotativo en data/siem_logs/ (local).
      2. [PROD] POST a un endpoint de ingestión (Splunk HEC, Elastic, etc.).

    Args:
        alert_data: Diccionario con los detalles del evento.
            Campos esperados:
              - threat_type (str): Ej. "Ataque_Mirai"
              - source_ip (str): IP origen del tráfico sospechoso
              - action_taken (str): Ej. "BLOCK", "ALLOW", "ALERT"
              - network_features (list): Vector de features analizadas
              - prediction_raw (str): Respuesta cruda del SLM

    Returns:
        dict con el resultado del registro.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Estructura CEF-like (Common Event Format) para interoperabilidad SIEM
    siem_event = {
        "timestamp": timestamp,
        "severity": _calculate_severity(alert_data.get("threat_type", "Unknown")),
        "event_type": "botnet_detection",
        "source": "langgraph_botnet_agent",
        "details": {
            "threat_type": alert_data.get("threat_type", "Unknown"),
            "source_ip": alert_data.get("source_ip", "N/A"),
            "action_taken": alert_data.get("action_taken", "NONE"),
            "network_features": alert_data.get("network_features", []),
            "prediction_raw": alert_data.get("prediction_raw", ""),
        },
    }

    # ── Persistencia local (.jsonl) ──
    jsonl_file = SIEM_LOG_DIR / "events.jsonl"
    with jsonl_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(siem_event, ensure_ascii=False) + "\n")

    logger.info(f"[SIEM] Evento registrado → severity={siem_event['severity']} | "
                f"threat={alert_data.get('threat_type')} | ip={alert_data.get('source_ip')}")

    # ── [PROD] Envío a Splunk HEC ──
    # import requests
    # SPLUNK_HEC_URL = "https://splunk.empresa.com:8088/services/collector/event"
    # SPLUNK_TOKEN = os.environ.get("SPLUNK_HEC_TOKEN", "")
    # requests.post(
    #     SPLUNK_HEC_URL,
    #     headers={"Authorization": f"Splunk {SPLUNK_TOKEN}"},
    #     json={"event": siem_event},
    #     timeout=10,
    # )

    # ── [PROD] Envío a Elastic SIEM ──
    # from elasticsearch import Elasticsearch
    # es = Elasticsearch(["https://elastic.empresa.com:9200"])
    # es.index(index="botnet-alerts", document=siem_event)

    return {
        "status": "logged",
        "log_file": str(jsonl_file),
        "severity": siem_event["severity"],
        "timestamp": timestamp,
    }


def _calculate_severity(threat_type: str) -> str:
    """Mapea el tipo de amenaza a un nivel de severidad SIEM estándar."""
    severity_map = {
        "Mirai": "HIGH",
        "Gafgyt": "HIGH",
        "Desconocido": "MEDIUM",
        "Error_Inferencia": "MEDIUM",
        "Error_Modelo_o_Datos": "LOW",
        "Normal": "INFO",
    }
    return severity_map.get(threat_type, "MEDIUM")
