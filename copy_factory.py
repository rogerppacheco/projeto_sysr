import os
import shutil

projects = ['nova-velox', 'site-bn', 'site-clickup', 'site-gm', 'site-rosso']
source_project = 'site-record'
base_dir = r"C:\Projeto_Sysr"

rel_path = r"crm_app\services\whatsapp\factory.py"

for p in projects:
    src = os.path.join(base_dir, source_project, rel_path)
    dst = os.path.join(base_dir, p, rel_path)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Copied {rel_path} to {p}")
