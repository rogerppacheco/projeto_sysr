import os
import shutil

projects = ['nova-velox', 'site-bn', 'site-clickup', 'site-gm', 'site-rosso']
source_project = 'site-record'
base_dir = r"C:\Projeto_Sysr"

files_to_sync = [
    r"crm_app\services\folha_comissionamento_cache.py",
]

for p in projects:
    for rel_path in files_to_sync:
        src = os.path.join(base_dir, source_project, rel_path)
        dst = os.path.join(base_dir, p, rel_path)
        if os.path.exists(src) and os.path.exists(os.path.dirname(dst)):
            shutil.copy2(src, dst)
            print(f"Copied {rel_path} to {p}")
