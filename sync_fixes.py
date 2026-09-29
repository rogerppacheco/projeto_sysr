import os
import shutil
import re

projects = ['nova-velox', 'site-bn', 'site-clickup', 'site-gm', 'site-rosso']
source_project = 'site-record'
base_dir = r"C:\Projeto_Sysr"

files_to_sync = [
    r"crm_app\tasks_celery.py",
    r"crm_app\services\pap_pool_service.py",
    r"usuarios\models.py",
    r"crm_app\services\pap_job_processor.py",
    r"Procfile",
    r"scripts\start_web.sh",
]

# 1. Sync the identical files
for p in projects:
    for rel_path in files_to_sync:
        src = os.path.join(base_dir, source_project, rel_path)
        dst = os.path.join(base_dir, p, rel_path)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {rel_path} to {p}")

# 2. Patch settings.py for CELERY_BEAT_SCHEDULE varredura
for p in projects:
    settings_path = os.path.join(base_dir, p, "core_config", "settings.py")
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        varredura_block = """    'varrer_jobs_pendentes_pap': {
        'task': 'crm_app.tasks_celery.varrer_jobs_pendentes_pap',
        'schedule': 15.0,  # A cada 15 segundos
    },
"""
        if "'varrer_jobs_pendentes_pap'" not in content:
            # Inject right before the closing brace of CELERY_BEAT_SCHEDULE
            content = re.sub(
                r"(\s*'args': \('lista_agendamento_vendedor_tarde',\)\n\s*})(\n)",
                r"\1,\n" + varredura_block + r"}\2",
                content
            )
            # Another try if it has a comma already
            content = re.sub(
                r"(\s*'args': \('lista_agendamento_vendedor_tarde',\)\n\s*},\n)(})",
                r"\1" + varredura_block + r"\2",
                content
            )
            
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched settings.py in {p}")

print("Sync completed.")
