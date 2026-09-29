import os
import re

projects = ['nova-velox', 'site-bn', 'site-clickup', 'site-gm', 'site-record', 'site-rosso']
base_dir = r"C:\Projeto_Sysr"

def inject_silk(project):
    settings_path = os.path.join(base_dir, project, "core_config", "settings.py")
    urls_path = os.path.join(base_dir, project, "core_config", "urls.py")
    reqs_path = os.path.join(base_dir, project, "requirements.txt")
    
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "'silk'" not in content:
            content = re.sub(
                r"(\s*'crm_app',)(\s*\])",
                r"\1\n    'silk',\2",
                content
            )
            
        if "'silk.middleware.SilkyMiddleware'" not in content:
            content = re.sub(
                r"(\s*'django\.middleware\.security\.SecurityMiddleware',)",
                r"\1\n    'silk.middleware.SilkyMiddleware',",
                content
            )
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    if os.path.exists(urls_path):
        with open(urls_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "'silk/'" not in content:
            content = re.sub(
                r"(urlpatterns\s*=\s*\[)",
                r"\1\n    path('silk/', include('silk.urls', namespace='silk')),",
                content
            )
        with open(urls_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    if os.path.exists(reqs_path):
        with open(reqs_path, 'r', encoding='utf-8') as f:
            reqs = f.read()
        if "django-silk" not in reqs:
            with open(reqs_path, 'a', encoding='utf-8') as f:
                f.write("\ndjango-silk==5.1.0\n")

def inject_cursor_pagination(project):
    views_path = os.path.join(base_dir, project, "crm_app", "views.py")
    if not os.path.exists(views_path): return
    
    with open(views_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "from rest_framework.pagination import CursorPagination" not in content:
        content = content.replace(
            "from rest_framework.pagination import PageNumberPagination",
            "from rest_framework.pagination import PageNumberPagination, CursorPagination"
        )
        
    kanban_class = """
class KanbanCursorPagination(CursorPagination):
    page_size = 30
    ordering = '-data_ultima_alteracao'
"""
    if "class KanbanCursorPagination" not in content:
        content = content.replace(
            "class VendaPagination(PageNumberPagination):",
            kanban_class + "\nclass VendaPagination(PageNumberPagination):"
        )
        
    prop_method = """
    @property
    def pagination_class(self):
        # A API tenta usar query_params em certos escopos onde não existe request.
        if not hasattr(self, 'request') or not self.request:
            return VendaPagination
            
        flow = getattr(self.request, 'query_params', {}).get('flow')
        if flow == 'esteira':
            return KanbanCursorPagination
        return VendaPagination
"""
    if "def pagination_class(self):" not in content:
        content = content.replace(
            "    pagination_class = VendaPagination",
            prop_method.lstrip('\n')
        )
        
    with open(views_path, 'w', encoding='utf-8') as f:
        f.write(content)

for p in projects:
    print(f"Processando {p}...")
    inject_silk(p)
    inject_cursor_pagination(p)
print("Concluído!")
