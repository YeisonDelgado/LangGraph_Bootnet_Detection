"""
data_loader.py — Descarga y procesa el dataset N-BaIoT dinámicamente.
Aplica sampling balanceado a las clases Normal, Mirai y Gafgyt.
"""

import pandas as pd
import glob
import kagglehub
from pathlib import Path
import logging
import random

logger = logging.getLogger("data_loader")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(ch)

# Features optimizados del modelo SLM entrenado (14 features finales)
FEATURES_UNIVERSAL = [
    "MI_dir_L0.1_weight", "MI_dir_L0.1_mean", "MI_dir_L0.01_weight", 
    "MI_dir_L0.01_mean", "H_L5_weight", "H_L1_mean", "H_L0.1_weight", 
    "H_L0.01_weight", "H_L0.01_mean", "HH_L1_weight", "HH_L0.1_covariance", 
    "HH_jit_L5_mean", "HH_jit_L0.1_mean", "HH_jit_L0.01_mean"
]

def map_label_from_filename(filename: str) -> str:
    """Asigna la etiqueta textual basado en el nombre del archivo"""
    name_lower = filename.lower()
    if 'benign' in name_lower:
        return 'Normal'
    elif 'mirai' in name_lower:
        return 'Mirai'
    elif 'gafgyt' in name_lower:
        return 'Gafgyt'
    return 'Desconocido'


def load_balanced_sample(samples_per_class: int = 10) -> pd.DataFrame:
    """
    Descarga el N-BaIoT if needed, busca los CSV por tipo, 
    extrae el número de muestras solicitadas y las empaqueta en un solo DataFrame evaluable.
    """
    logger.info("📡 Verificando/Descargando N-BaIoT Dataset vía kagglehub...")
    path = kagglehub.dataset_download("mkashifn/nbaiot-dataset")
    csv_files = glob.glob(f"{path}/**/*.csv", recursive=True)
    
    if not csv_files:
        raise FileNotFoundError(f"No se encontraron archivos CSV en la ruta: {path}")

    # Agrupar archivos por tipo de etiqueta
    archivos_por_clase = {'Normal': [], 'Mirai': [], 'Gafgyt': []}
    
    for f in csv_files:
        label = map_label_from_filename(Path(f).name)
        if label in archivos_por_clase:
            archivos_por_clase[label].append(f)

    logger.info(f"📁 Encontrados {len(archivos_por_clase['Normal'])} benigns, "
                f"{len(archivos_por_clase['Mirai'])} mirai, "
                f"{len(archivos_por_clase['Gafgyt'])} gafgyt.")

    df_list = []
    
    for clase, archivos in archivos_por_clase.items():
        if not archivos:
            logger.warning(f"No hay archivos para la clase {clase}!")
            continue
            
        logger.info(f"⏱️ Extrayendo {samples_per_class} muestras de clase {clase}...")
        
        # Para evitar abrir archivos gigantes y colapsar RAM, abrimos solo uno aleatorio y tomamos submuestras
        target_file = random.choice(archivos)
        
        try:
            # Leer únicamente las columnas necesarias. Toma una pequeña muestra aleatoria.
            # Se usa skiprows aleatorio o simplemente sample
            # pd.read_csv optimizado leyendo todo y pidiendo sample (los ficheros CSV individuales son manejables)
            temp_df = pd.read_csv(target_file, usecols=FEATURES_UNIVERSAL)
            
            # Asegurarse que haya suficientes filas
            n_samples_available = min(len(temp_df), samples_per_class)
            sampled_df = temp_df.sample(n=n_samples_available, random_state=42)
            
            # Ya no se instancia ni escala por bloques. El escalado se hará global usando el modelo pre-entrenado.
            
            # Inyectar etiqueta
            sampled_df['true_label'] = clase
            sampled_df['file_source'] = Path(target_file).name
            
            df_list.append(sampled_df)
            
        except ValueError as e:
            logger.error(f"Error procesando {target_file}. ¿Faltan columnas de FEATURES_UNIVERSAL? {e}")

    if not df_list:
        raise RuntimeError("No se pudo extraer ninguna muestra de datos válida.")

    # Combinar y desordenar para evitar sesgo secuencial en la evaluación
    final_df = pd.concat(df_list, ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Cargar y aplicar el RobustScaler matemático exacto que generó Colab
    import joblib
    scaler_path = Path(__file__).resolve().parent.parent.parent / "modelos_entrenados" / "robust_scaler.pkl"
    if scaler_path.exists():
        logger.info("🔧 Aplicando RobustScaler() pre-entrenado a todas las características...")
        scaler = joblib.load(scaler_path)
        # scale.transform output es ndarray, asignamos preservando las columnas para el inyector del prompt
        final_df[FEATURES_UNIVERSAL] = scaler.transform(final_df[FEATURES_UNIVERSAL])
        logger.info(f"✅ Extracción completada. {len(final_df)} registros balanceados y escalados idénticos a Fine-Tuning.")
    else:
        logger.warning(f"⚠️ No se encontró {scaler_path.name}, asegúrate de colocar el archivo. Devolviendo datos sin escalar.")
        
    return final_df

if __name__ == "__main__":
    df = load_balanced_sample()
    print(df.head())
