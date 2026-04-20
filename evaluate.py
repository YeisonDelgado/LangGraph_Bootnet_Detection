"""
evaluate.py — Ejecuta evaluación masiva del modelo SLM usando LangGraph y el entorno real.
"""

import sys
import pandas as pd
import logging
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

from src.utils.data_loader import load_balanced_sample, FEATURES_UNIVERSAL
from src.graph.workflow import botnet_agent
from src.graph.state import BotnetState

# Rutas
PROJECT_ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("evaluator")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
logger.addHandler(ch)

def plot_confusion_matrix(y_true, y_pred, classes):
    """Guarda imagen de la Matriz de Confusión"""
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.title('Matriz de Confusión - Detección Edge Botnets')
    plt.ylabel('Etiqueta Real')
    plt.xlabel('Predicción de Qwen2.5 (LangGraph)')
    plt.tight_layout()
    
    output_path = PROCESSED_DIR / "confusion_matrix.png"
    plt.savefig(output_path, dpi=300)
    logger.info(f"📈 Matriz de confusión guardada en: {output_path}")

def main():
    print("=" * 60)
    print("🔬 MODO EVALUACIÓN: LangGraph + Dataset N-BaIoT Real")
    print("=" * 60)
    
    try:
        # Cargar dataset (10 por clase por defecto)
        samples_per_class = 10
        df_eval = load_balanced_sample(samples_per_class=samples_per_class)
    except Exception as e:
        logger.error(f"Error cargando dataset: {e}")
        sys.exit(1)

    y_true = []
    y_pred = []
    
    total = len(df_eval)
    
    for idx, row in df_eval.iterrows():
        true_label = row['true_label']
        
        # Extraer vector asegurando el orden correcto
        vector_red = [float(row[col]) for col in FEATURES_UNIVERSAL]
        
        logger.info(f"[{idx+1}/{total}] Simulando tráfico desde {row['file_source']} (Esperado: {true_label})")
        
        estado_inicial: BotnetState = {
            "messages": [],
            "network_data": vector_red,
            "source_ip": f"192.168.1.{100 + idx}",  # IP Fake para logs
            "prediction": "",
            "security_action": "",
            "actions_log": [],
        }

        # Invocar flujo
        resultado = botnet_agent.invoke(estado_inicial)
        predicted_label = resultado['prediction']
        
        # Si predice "Desconocido" u otro output fallido, considerarlo Error para la matriz
        y_true.append(true_label)
        y_pred.append(predicted_label)
        
        logger.info(f"   → Predicción SLM: {predicted_label} | Acción Defensiva: {resultado['security_action']}")

    # ── Reporte de Resultados ──
    print("\n" + "=" * 60)
    print("📊 REPORTE DE CLASIFICACIÓN FINAL")
    print("=" * 60)
    
    report = classification_report(y_true, y_pred, zero_division=0)
    print(report)
    
    # Exportar resultados numéricos a texto
    report_file = PROCESSED_DIR / "evaluate_report.txt"
    report_file.write_text("Reporte de Evaluación N-BaIoT Edge\n" + "="*30 + "\n" + report, encoding="utf-8")
    
    # Generar Matriz Gráfica
    plot_confusion_matrix(y_true, y_pred, classes=["Normal", "Mirai", "Gafgyt"])
    print("=" * 60)
    print(f"✅ Evaluación finalizada con {total} registros. Revisa la carpeta data/processed/")

if __name__ == "__main__":
    main()
