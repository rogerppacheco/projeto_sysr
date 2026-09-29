import json
import os
import csv

input_json = r'c:\Projeto_Sysr\diff_report.json'
output_csv = r'C:\Users\rogge\.gemini\antigravity-ide\brain\cf93cfde-5e8b-460d-99cd-6845890584f5\function_mapping.csv'
output_md = r'C:\Users\rogge\.gemini\antigravity-ide\brain\cf93cfde-5e8b-460d-99cd-6845890584f5\function_mapping.md'

projects = ['nova-velox', 'site-bn', 'site-clickup', 'site-gm', 'site-record', 'site-rosso']
ignore_patterns = ['.chrome_cdp_tmp', 'pap_sessions', 'scratch', 'docs', 'assets', '.github']

with open(input_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

md_lines = ["# Mapeamento de Funções Python\n"]
md_lines.append("Abaixo está a matriz de funções para os arquivos Python que apresentam diferenças entre os projetos.\n")
md_lines.append("Isso ajudará a mapear e decidir quais funções específicas devem ser unificadas ou mantidas de forma isolada.\n\n")

csv_data = [["Arquivo", "Função/Classe"] + projects]

has_diffs = False

for filepath, info in sorted(data.items()):
    if not filepath.endswith('.py'):
        continue
    if any(ip in filepath for ip in ignore_patterns):
        continue
    
    # Check if there's any actual function difference
    all_funcs_in_file = set()
    proj_funcs = {}
    for p in projects:
        p_info = info.get(p)
        if p_info:
            funcs = set(p_info.get('functions', []))
            proj_funcs[p] = funcs
            all_funcs_in_file.update(funcs)
        else:
            proj_funcs[p] = set()
    
    if not all_funcs_in_file:
        continue
        
    # Check if functions are identical across ALL 6 projects
    identical = True
    # Instead of first_funcs, just pick the first project that has any functions or just check all against each other
    reference = proj_funcs[projects[0]]
    for p in projects:
        if proj_funcs[p] != reference:
            identical = False
            break
            
    if identical:
        # no function difference across the 6 projects
        continue

    has_diffs = True
    md_lines.append(f"## {filepath}\n")
    md_lines.append("| Função / Classe | " + " | ".join(projects) + " |")
    md_lines.append("|---" + "|---" * len(projects) + "|")

    for func in sorted(all_funcs_in_file):
        row = [filepath, func]
        md_row = [f"`{func}`"]
        for p in projects:
            if func in proj_funcs[p]:
                row.append("Sim")
                md_row.append("✅")
            else:
                row.append("Não")
                md_row.append("❌")
        csv_data.append(row)
        md_lines.append("| " + " | ".join(md_row) + " |")
    md_lines.append("\n")

if not has_diffs:
    md_lines.append("> Não foram encontradas discrepâncias de funções Python entre os projetos analisados.")

with open(output_csv, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(csv_data)

with open(output_md, 'w', encoding='utf-8') as f:
    f.write("\n".join(md_lines))

print("Mappings generated.")
