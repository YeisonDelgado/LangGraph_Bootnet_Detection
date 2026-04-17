# Prueba Entrenamiento LangGraph

Proyecto para el entrenamiento y fine-tuning de modelos (ej. Lora, QLoRa) integrados con LangGraph.

## Estructura del Proyecto

Basado en las mejores prácticas para proyectos de Data Science e Inteligencia Artificial:

- **`data/`**: Carpeta para almacenar conjuntos de datos.
  - **`raw/`**: Datos crudos u originales, inmutables.
  - **`processed/`**: Datos limpios y procesados listos para entrenamiento o inferencia.
- **`notebooks/`**: Cuadernos interactivos de Jupyter (ej. análisis exploratorios, pruebas de concepto como `Fine_Tuned_QLoRa.ipynb`).
- **`src/`**: Código fuente principal del proyecto.
  - **`models/`**: Scripts de configuración, entrenamiento y fine-tuning de modelos (LoRa, QLoRa, etc.).
  - **`graph/`**: Definición de la lógica de negocio de LangGraph (nodos, aristas, estado).
  - **`tools/`**: Herramientas (Tools) a ser utilizadas por los agentes de LangGraph/Langchain.
  - **`utils/`**: Funciones auxiliares o de uso general.
- **`config/`**: Archivos de configuración (ej. hiperparámetros, variables de entorno, configuraciones de LangGraph).
- **`tests/`**: Pruebas unitarias y de integración para garantizar el funcionamiento del sistema.
- **`docs/`**: Documentación del proyecto.

## Uso

1. Coloca tus scripts de entrenamiento en `src/models/`.
2. Mueve tus libretas actuales a `notebooks/`.
3. Desarrolla la orquestación del agente en `src/graph/`.
