import os
import subprocess

projects = ['nova-velox', 'site-bn', 'site-clickup', 'site-gm', 'site-record', 'site-rosso']
base_dir = r"C:\Projeto_Sysr"

for p in projects:
    path = os.path.join(base_dir, p)
    print(f"Commiting and pushing {p}...")
    subprocess.run(["git", "add", "."], cwd=path)
    subprocess.run(["git", "commit", "-m", "feat: implementado django-silk para auditoria N+1 e CursorPagination no Kanban"], cwd=path)
    subprocess.run(["git", "push"], cwd=path)
    print(f"{p} DONE\n")
