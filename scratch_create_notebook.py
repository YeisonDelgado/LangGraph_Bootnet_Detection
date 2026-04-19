import json
import os

notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Exportable a Ollama (GGUF): SLM Causal Fine-Tuning\n",
    "Este notebook cambia radicalmente la manera en que entrenamos el modelo para **garantizar compatibilidad nativa con Ollama y GGUF**.\n",
    "\n",
    "En lugar de sustituir el Tokenizador por una entrada numérica tabular, convertiremos la tabla de las estadísticas de red en **Prompts de Texto instructivo** y utilizaremos un modelo Causal tradicional."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Instalación de Dependencias e Importaciones"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "!pip install -q kagglehub transformers datasets peft accelerate trl\n",
    "!git clone https://github.com/ggerganov/llama.cpp.git || true\n",
    "!pip install -q -r llama.cpp/requirements.txt\n",
    "\n",
    "import pandas as pd\n",
    "import torch\n",
    "import os\n",
    "import glob\n",
    "from datasets import Dataset\n",
    "from peft import LoraConfig, get_peft_model, PeftModel\n",
    "from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments\n",
    "from trl import SFTTrainer\n",
    "import kagglehub\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Preparación de Datos: Tabular -> Texto Explicativo (Prompting)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Limitamos datos por propósitos de prueba para ver el concepto\n",
    "MUESTRAS_BENIGN = 1000\n",
    "MUESTRAS_ATAQUE = 500\n",
    "\n",
    "path = kagglehub.dataset_download(\"mkashifn/nbaiot-dataset\")\n",
    "\n",
    "def cargar_y_convertir_a_texto(patron, label_texto, limite):\n",
    "    archivos = glob.glob(os.path.join(path, '**', patron), recursive=True)\n",
    "    if not archivos: archivos = glob.glob(os.path.join(path, patron))\n",
    "    if not archivos: return []\n",
    "    \n",
    "    prompts = []\n",
    "    for f in archivos:\n",
    "        try:\n",
    "            df = pd.read_csv(f, nrows=limite)\n",
    "            # Solo utilizamos un par de features para no hacer el prompt larguísimo\n",
    "            features_to_use = ['MI_dir_L5_weight', 'H_L5_weight', 'HH_L0.01_std']\n",
    "            \n",
    "            for _, row in df.iterrows():\n",
    "                # Convertimos la estadística a texto puro que el SLM pueda \"LEER\"\n",
    "                input_text = f\"Analiza este trafico: MI_dir_L5: {row.get('MI_dir_L5_weight', 0):.2f}, H_L5: {row.get('H_L5_weight', 0):.2f}, HH_L0.01: {row.get('HH_L0.01_std', 0):.2f}.\"\n",
    "                salida = label_texto\n",
    "                \n",
    "                # Formato Chat estandar\n",
    "                prompt_completo = f\"<|user|>\\n{input_text}\\n<|assistant|>\\nEl tipo de trafico detectado es: {salida}<|endoftext|>\"\n",
    "                prompts.append({'text': prompt_completo})\n",
    "                \n",
    "                if len(prompts) >= limite: break\n",
    "        except Exception as e:\n",
    "            pass\n",
    "        if len(prompts) >= limite: break\n",
    "    return prompts\n",
    "\n",
    "datos_benignos = cargar_y_convertir_a_texto('*.benign.csv', 'Normal', MUESTRAS_BENIGN)\n",
    "datos_mirai = cargar_y_convertir_a_texto('*.mirai.*.csv', 'Ataque_Mirai', MUESTRAS_ATAQUE)\n",
    "\n",
    "dataset_text = datos_benignos + datos_mirai\n",
    "hf_dataset = Dataset.from_list(dataset_text).shuffle(seed=42)\n",
    "print(\"Muestra del Prompt:\\n\", hf_dataset[0]['text'])"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Cargar Modelo Generativo (Ej. Qwen2.5-0.5B) y Entrenamiento LoRA (SFTTrainer)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "modelo_id = \"Qwen/Qwen2.5-0.5B-Instruct\"\n",
    "tokenizer = AutoTokenizer.from_pretrained(modelo_id)\n",
    "tokenizer.pad_token = tokenizer.eos_token\n",
    "\n",
    "model = AutoModelForCausalLM.from_pretrained(modelo_id, device_map=\"auto\", torch_dtype=torch.float16)\n",
    "\n",
    "peft_config = LoraConfig(\n",
    "    r=16, \n",
    "    lora_alpha=32,\n",
    "    target_modules=[\"q_proj\", \"v_proj\"],\n",
    "    task_type=\"CAUSAL_LM\"\n",
    ")\n",
    "\n",
    "training_args = TrainingArguments(\n",
    "    output_dir=\"./lora_output\",\n",
    "    per_device_train_batch_size=8,\n",
    "    gradient_accumulation_steps=4,\n",
    "    num_train_epochs=1,\n",
    "    logging_steps=10,\n",
    "    learning_rate=2e-4,\n",
    "    save_steps=50,\n",
    ")\n",
    "\n",
    "trainer = SFTTrainer(\n",
    "    model=model,\n",
    "    train_dataset=hf_dataset,\n",
    "    dataset_text_field=\"text\",\n",
    "    max_seq_length=128,\n",
    "    peft_config=peft_config,\n",
    "    args=training_args\n",
    ")\n",
    "\n",
    "print(\"Iniciando el entrenamiento...\")\n",
    "trainer.train()\n",
    "trainer.model.save_pretrained(\"./lora_botnet_final\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 4. FUSIÓN: Juntar el Modelo Base con el Adaptador LoRA"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import gc\n",
    "del model, trainer\n",
    "gc.collect()\n",
    "torch.cuda.empty_cache()\n",
    "\n",
    "# Recargar el Base Model\n",
    "base_model = AutoModelForCausalLM.from_pretrained(modelo_id, torch_dtype=torch.float16, device_map=\"cpu\")\n",
    "\n",
    "# Montar LoRA\n",
    "modelo_fusionable = PeftModel.from_pretrained(base_model, \"./lora_botnet_final\")\n",
    "\n",
    "# IMPORTANTE: Hacer un Merge físico de los tensores\n",
    "modelo_fusionado = modelo_fusionable.merge_and_unload()\n",
    "\n",
    "# Guardar en formato explícito nativo HF\n",
    "modelo_fusionado.save_pretrained(\"../modelos_entrenados/Botnet_Merged_HF\")\n",
    "tokenizer.save_pretrained(\"../modelos_entrenados/Botnet_Merged_HF\")\n",
    "print(\"✅ Modelo HF consolidado y guardado en disco.\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 5. Convertir el Base HF a GGUF para Ollama (Llama.cpp)\n",
    "Ejecutaremos el script oficial que empaqueta todo el modelo, tensores y tokenizador a un único `.gguf` local."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Exportar modelo base al estándar Q8_0 de GGUF\n",
    "print(\"Iniciando conversion a GGUF...\")\n",
    "\n",
    "!\n",
    "!python llama.cpp/convert_hf_to_gguf.py ../modelos_entrenados/Botnet_Merged_HF --outfile ../modelos_entrenados/botnet_Qwen.gguf --outtype q8_0\n",
    "\n",
    "print(\"\\n\\n✅ \\U0001f389 Modelo listo! Revisa ../modelos_entrenados/botnet_Qwen.gguf\")\n",
    "print(\"Puedes mover botnet_Qwen.gguf a cualquier PC y crear un Ollama Modelfile así:\\n\")\n",
    "print(\"FROM ./botnet_Qwen.gguf\")\n",
    "print(\"TEMPLATE \\\"<|user|>\\n{{ .Prompt }}\\n<|assistant|>\\n\\\"\")\n",
    "print(\"PARAMETER temperature 0.1\")\n",
    "print(\"\\Y luego ejecutar: ollama create mi_botnet -f Modelfile\")\n"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.10.12"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

import pathlib

notebook_dir = pathlib.Path(__file__).parent / "notebooks"
notebook_dir.mkdir(parents=True, exist_ok=True)
file_path = notebook_dir / "Fine_Tuned_GGUF_Ollama.ipynb"

with file_path.open('w', encoding='utf-8') as f:
    json.dump(notebook_content, f, indent=1, ensure_ascii=False)
    f.write('\n')
print(f"Creado: {file_path}")
