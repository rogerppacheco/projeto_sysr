import json
import os

input_json = r'c:\Projeto_Sysr\diff_report.json'
output_md = r'C:\Users\rogge\.gemini\antigravity-ide\brain\cf93cfde-5e8b-460d-99cd-6845890584f5\analysis_results.md'

projects = ['nova-velox', 'site-bn', 'site-clickup', 'site-gm', 'site-record', 'site-rosso']

# Directories or strings we want to completely ignore in the final report
ignore_patterns = ['.chrome_cdp_tmp', 'pap_sessions', 'scratch', 'docs', 'assets', '.github']

with open(input_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

filtered_data = {}
for filepath, info in data.items():
    if any(ip in filepath for ip in ignore_patterns):
        continue
    # skip some purely static or compiled stuff if any
    filtered_data[filepath] = info

md_lines = ["# Análise de Diferenças entre Projetos\n"]
md_lines.append("Esta análise compara as funções e contagem de linhas entre os 6 projetos: " + ", ".join(projects) + ".\n")
md_lines.append("Os arquivos listados abaixo possuem alguma diferença (linhas de código ou funções) entre os projetos ou não existem em todos eles.\n")

# Group by first folder
by_folder = {}
for filepath, info in filtered_data.items():
    parts = filepath.split('/')
    if len(parts) > 1:
        folder = parts[0]
    else:
        folder = 'Raiz (Root)'
        
    if folder not in by_folder:
        by_folder[folder] = {}
    by_folder[folder][filepath] = info

for folder in sorted(by_folder.keys()):
    md_lines.append(f"## Pasta: `{folder}`\n")
    
    for filepath in sorted(by_folder[folder].keys()):
        info = by_folder[folder][filepath]
        md_lines.append(f"### `{filepath}`\n")
        
        md_lines.append("| Projeto | Linhas de Código | Funções/Classes |")
        md_lines.append("|---------|------------------|-----------------|")
        
        for proj in projects:
            p_info = info.get(proj)
            if p_info is None:
                md_lines.append(f"| {proj} | Ausente | Ausente |")
            else:
                loc = p_info.get('loc', 0)
                funcs = p_info.get('functions', [])
                funcs_str = str(len(funcs)) + " funções" if funcs else "-"
                # To not make it too huge, let's just list the count of functions.
                # If they want details, they can check code. But the prompt said "diferenças de funções"
                # Let's show the list of functions if it's small, or just count.
                if funcs:
                    if len(funcs) <= 10:
                        funcs_str = ", ".join(funcs)
                    else:
                        funcs_str = f"{len(funcs)} funções"
                        
                md_lines.append(f"| {proj} | {loc} | {funcs_str} |")
        md_lines.append("\n")

with open(output_md, 'w', encoding='utf-8') as f:
    f.write("\n".join(md_lines))

print(f"Relatório gerado em: {output_md}")
