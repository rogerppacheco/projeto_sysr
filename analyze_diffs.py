import os
import ast
import json
import re

projects = ['nova-velox', 'site-bn', 'site-clickup', 'site-gm', 'site-record', 'site-rosso']
base_dir = r'c:\Projeto_Sysr'
CODE_EXTENSIONS = {'.py', '.js', '.html', '.css', '.txt', '.json', '.md'}

def get_code_files(project_path):
    code_files = {}
    for root, _, files in os.walk(project_path):
        if '.venv' in root or '__pycache__' in root or '.git' in root or 'node_modules' in root or 'migrations' in root:
            continue
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in CODE_EXTENSIONS:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_path)
                # Convert backslash to slash for consistency
                rel_path = rel_path.replace('\\', '/')
                code_files[rel_path] = full_path
    return code_files

def extract_info(filepath, ext):
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        lines = content.splitlines()
        line_count = len(lines)
        
        functions = set()
        if ext == '.py':
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                        functions.add(node.name)
                    elif isinstance(node, ast.ClassDef):
                        for subnode in node.body:
                            if isinstance(subnode, ast.FunctionDef) or isinstance(subnode, ast.AsyncFunctionDef):
                                functions.add(f"{node.name}.{subnode.name}")
            except:
                pass # Parse error
                
        return functions, line_count
    except Exception as e:
        return set(), 0

all_files = set()
project_files = {}

for proj in projects:
    proj_path = os.path.join(base_dir, proj)
    if os.path.exists(proj_path):
        pf = get_code_files(proj_path)
        project_files[proj] = pf
        all_files.update(pf.keys())

report = {}

for rel_path in sorted(all_files):
    ext = os.path.splitext(rel_path)[1].lower()
    file_info = {}
    for proj in projects:
        if proj in project_files and rel_path in project_files[proj]:
            filepath = project_files[proj][rel_path]
            funcs, loc = extract_info(filepath, ext)
            file_info[proj] = {'functions': list(funcs), 'loc': loc}
        else:
            file_info[proj] = None
    
    # Check for differences
    present_projs = [p for p in projects if file_info[p] is not None]
    if len(present_projs) == 0:
        continue
        
    first_proj = present_projs[0]
    base_funcs = set(file_info[first_proj]['functions'])
    base_loc = file_info[first_proj]['loc']
    
    is_diff = False
    if len(present_projs) != len(projects):
        is_diff = True # Missing in some projects
    else:
        for proj in projects:
            if proj == first_proj: continue
            if set(file_info[proj]['functions']) != base_funcs or file_info[proj]['loc'] != base_loc:
                is_diff = True
                break
                
    if is_diff:
        report[rel_path] = file_info

with open(r'c:\Projeto_Sysr\diff_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=4)

print("Report generated at diff_report.json")
