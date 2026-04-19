import json

file_path = r'c:\Users\alexi\Documents\Proyectos2026\Software_projects\EntrenamientoModelos\LangGraph_Bootnet_Detection\notebooks\Fine_Tuned_Lora.ipynb'

with open(file_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb.get('cells', []):
    if cell.get('cell_type') == 'code':
        source = cell.get('source', [])
        
        new_source = []
        for line in source:
            new_source.append(line)
            # Find the line that prints the metric, we'll insert the save logic right after the epochs finish
            if "print(f\"✅ LoRA - Epoch {epoch} | F1:" in line:
                new_source.append("\n")
                new_source.append("        # Guardar el modelo en disco (adaptadores LoRA)\n")
                new_source.append("        path_guardado = f\"../modelos_entrenados/{nombre}_LoRA\"\n")
                new_source.append("        model.save_pretrained(path_guardado)\n")
                new_source.append("        print(f\"\\U0001f4be Modelo guardado en: {path_guardado}\\n\")\n")

        # Because the previous print is IN the for epoch loop, wait.
        pass
