# Sistema Inteligente de Detección de Botnets Edge (LangGraph + Qwen2.5)

Este proyecto desarrolla un agente de ciberseguridad impulsado por Inteligencia Artificial "Edge", orquestado mediante **LangGraph**, diseñado específicamente para analizar y clasificar tráfico de protocolos IoT y detectar patrones característicos de botnets (como Mirai y Gafgyt) usando el framework estadístico **N-BaIoT**.

El enfoque principal de la tesis es descentralizar el poder de cómputo ubicando pequeñas ventanas de inferencia al "Borde" o "Edge". Para esto, el proyecto incorpora un **Small Language Model (SLM)**, en este caso el modelo local **Qwen2.5 (8-bits)** con Fine-Tuning específico de clasificación a partir de tensores de red en formato vectorial. Se utiliza `langchain-ollama` para hacer bypass de los APIs en la nube limitando el lag y blindando la privacidad de la red local.

---

## 🎯 ¿Qué Resuelve?
- **Descentralización y Privacidad:** Al utilizar Qwen2.5 en formato GGUF empaquetado a través de Ollama en local, los logs crudos con información confidencial o IPs de la red nunca se comunican a la nube (ej. OpenAI/Anthropic), preservándose in-house.
- **Reducción de Latencia:** Evita el cuello de botella que introducen los Tiempos de Ida y Vuelta (Round Trip Time, RTT) en entornos Cloud, crucial cuando de detección de ataques de denegación de servicio distribuido (DDoS) se trata.
- **Orquestación con GenAI:** Desmitifica la idea de que los LLMs son solo conversacionales, transformándolos en **agentes decisionales** dentro de una pipeline graficada (LangGraph).

---

## 🛠 Estructura del Proyecto

```text
Prueba Entrenamiento LangGraph/
├── .venv/                         # Entorno virtual con dependencias acopladas
├── config/                        # Configuraciones, variables y tokens (Drive API)
├── data/                          # Dataset N-BaIoT, vectores crudos y Dataframes
│   ├── processed/                 
│   ├── raw/
│   └── siem_logs/                 # Salida CEF de eventos por Firewall actions
├── docs/                          # Tesis o informes relacionados (LaTeX/PDF)
├── modelos_entrenados/            # SLMs descargados
│   ├── qwen2.5_botnet.gguf        # Peso del modelo con Fine-Tuning a medida
│   └── Modelfile                  # Plantilla de inicialización de ChatML
├── notebooks/                     # Exploración (Fine_Tuned_QLoRa.ipynb, extracciones)
├── src/                           # Código Fuente 
│   ├── graph/                     # Core del Sistema
│   │   ├── nodes.py               # Extractores, Clasificación SLM y Firewall
│   │   ├── state.py               # Objeto de Estado del Grafo (BotnetState)
│   │   └── workflow.py            # Orquestador LangGraph Principal
│   ├── models/                    
│   │   └── model_loader.py        # Instancia `ChatOllama` y Templates de N-BaIoT
│   ├── tools/
│   │   └── firewall_actions.py    # Logs de SIEM local y mitigaciones simuladas SSH
│   └── utils/
│       └── drive_uploader.py      # Puente hacia GCP Drive usando oauth-lib 
├── main.py                        # Entrypoint de prueba y terminal
├── README.md                      # Esta Documentación
└── requirements.txt               # Dependencias PIP
```

---

## ⚙️ Implementación Actual

1. **Inyección Vectorial Simulada (N-BaIoT):** El sistema (`main.py`) empuja actualmente 15 características numéricas infladas y relativas correspondientes a un escenario pasivo-agresivo (TCP SYN / UDP Flood) típico en la huella de **Mirai**.
2. **Pipelines Node:** LangGraph mapea secuencialmente los 15 floats en un String Template estricto y pasa la orden en background al modelo GGUF utilizando LangChain.
3. **Validación Output:** El LLM detecta el patron numérico del vector y arroja `Mirai`, instanciando el evento en el estado global.
4. **Respuesta Automática (Automated Response):** El nodo de orquestación final detecta el input como evento ofensivo, ejecuta el simulacro de IPTables bloqueando la IP y almacena la evidencia bajo formato log-SIEM en `data/siem_logs/events.jsonl`.
5. **Autosave a Cloud:** Herramientas asíncronas para transferir los Notebooks generadores de la tesis hacia Google Drive para control de versiones utilizando OAuth.

---

## 🚀 Requisitos e Instalación

### Prerrequisitos
- **Python 3.10+ o superior**.
- **Ollama Engine v0.1.3+** previamente instalado para servir los pesos GGUF localmente.

### Instrucciones

1. **Activa un entorno virtual** estricto:
```powershell
py -m venv .venv
.\.venv\Scripts\activate
```

2. **Instala las Dependencias Core**:
```powershell
pip install -r requirements.txt
```

3. **Carga el Modelo GGUF con Ollama**:
Debes tener el binario local del fine-tuning `qwen2.5_botnet.gguf` metido en la carperta `/modelos_entrenados/` y entonces armar la imagen OCI del modelo con su Modelfile respectivo:
```powershell
ollama create qwen2.5_botnet -f modelos_entrenados/Modelfile
```
*Si tienes la terminal activa, no olvides ejecutar `ollama serve` de fondo si el servicio no corre automáticamente.*

4. **Ejecuta la Inferencia:**
```powershell
python main.py
```
> En tu terminal visualizarás el paso del vector, el análisis del LLM de manera oculta y el resultado del Firewall.

---

## ⚠️ Lo que vas a Encontrar
- Todas las inyecciones generativas actualmente se rinden sobre el LLM parametrizando la temperatura estáticamente a `T=0.1`. Esto garantiza **Altísimo Determinismo** logrando consistencia para no perturbar ni alucinar la clasificación. 
- La arquitectura está pensada explícitamente sobre LangGraph para integraciones de Replicación Local (Loci y Threads). Si planeas guardar métricas (Checkpointing a SqLite/Postgres) simplemente basta modificar el Graph Compiler de LangGraph. 

