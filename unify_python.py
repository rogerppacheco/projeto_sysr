import os
import ast
import json
import shutil

projects = ['nova-velox', 'site-bn', 'site-clickup', 'site-gm', 'site-record', 'site-rosso']
base_dir = r'c:\Projeto_Sysr'
ignore_patterns = ['.chrome_cdp_tmp', 'pap_sessions', 'scratch', 'docs', 'assets', '.github']

def extract_top_level_blocks(source_code):
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return {}
    
    blocks = {}
    lines = source_code.splitlines()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            if node.decorator_list:
                start = node.decorator_list[0].lineno - 1
            end = node.end_lineno
            # keep trailing blank lines if possible, but let's just strictly use end_lineno
            block_code = '\n'.join(lines[start:end])
            blocks[node.name] = {
                'start': start,
                'end': end,
                'code': block_code,
                'len': len(block_code.strip()),
                'type': type(node).__name__
            }
    return blocks

def unify_file(rel_path):
    # Gather all versions
    versions = {}
    for proj in projects:
        filepath = os.path.join(base_dir, proj, rel_path)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                versions[proj] = f.read()
                
    if not versions:
        return
        
    # Find base version (the one with the most lines overall)
    base_proj = max(versions.keys(), key=lambda p: len(versions[p].splitlines()))
    base_code = versions[base_proj]
    
    base_blocks = extract_top_level_blocks(base_code)
    
    # We will reconstruct the file by doing replacements or appends
    # To replace safely, we can do it from bottom to top to not mess up line numbers,
    # OR we can just use string replacement if we assume exact block matches, but that's risky.
    # Better: split base_code into lines, and replace slices.
    
    # Find "better" or missing blocks
    replacements = {} # name -> code
    appends = [] # code
    
    for proj, code in versions.items():
        if proj == base_proj:
            continue
        blocks = extract_top_level_blocks(code)
        for name, info in blocks.items():
            if name not in base_blocks:
                # Missing in base, append it
                # check if we already decided to append it from another project
                if not any(name in a for a in appends):
                    appends.append(f"\n# Injetado de {proj}\n" + info['code'] + "\n")
                base_blocks[name] = info # mark as seen
            else:
                # Exists in base, check if "better" (longer code)
                # We use character length as a simple heuristic for "more features"
                current_best_len = base_blocks[name]['len']
                if name in replacements:
                    current_best_len = len(replacements[name].strip())
                    
                if info['len'] > current_best_len:
                    replacements[name] = info['code']
                    # update base_blocks so we track the new best length
                    base_blocks[name]['len'] = info['len']

    if not replacements and not appends:
        # No changes needed for base, just copy base to all
        final_code = base_code
    else:
        # Apply replacements from bottom to top
        lines = base_code.splitlines()
        # Sort replacements by start line descending
        reps = []
        for name, new_code in replacements.items():
            # get original boundaries from base_blocks (wait, base_blocks has original start/end)
            # but if it was replaced, the start/end in base_blocks is from the OTHER project.
            # We need the original base boundaries.
            # Let's re-extract base blocks to get pristine boundaries
            pass
            
        pristine_base_blocks = extract_top_level_blocks(base_code)
        to_replace = []
        for name, new_code in replacements.items():
            if name in pristine_base_blocks:
                to_replace.append({
                    'start': pristine_base_blocks[name]['start'],
                    'end': pristine_base_blocks[name]['end'],
                    'code': new_code
                })
        
        to_replace.sort(key=lambda x: x['start'], reverse=True)
        for rep in to_replace:
            lines[rep['start']:rep['end']] = rep['code'].splitlines()
            
        final_code = '\n'.join(lines) + "\n" + "".join(appends)

    # Now write final_code to all 6 projects
    for proj in projects:
        filepath = os.path.join(base_dir, proj, rel_path)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_code)

def main():
    with open(r'c:\Projeto_Sysr\diff_report.json', 'r', encoding='utf-8') as f:
        diff_report = json.load(f)
        
    for rel_path, info in diff_report.items():
        if not rel_path.endswith('.py'):
            continue
        if any(ip in rel_path for ip in ignore_patterns):
            continue
            
        # Unify this file
        print(f"Unificando: {rel_path}")
        try:
            unify_file(rel_path)
        except Exception as e:
            print(f"Erro em {rel_path}: {e}")

if __name__ == '__main__':
    main()
