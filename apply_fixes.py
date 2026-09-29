import os
import subprocess

PROJECTS = [
    "site-rosso",
    "site-clickup",
    "site-gm",
    "site-bn",
    "nova-velox"
]

BASE_DIR = r"c:\Projeto_Sysr"

CELERY_CONFIG = """
# Configurações do Celery
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
"""

WEBHOOK_TARGET = """            if msg == "no_results" or not detalhes:
                whatsapp.enviar_mensagem_texto(
                    telefone,
                    "📡 *Status online (PAP)*\\n\\n"
                    "Não tem pedido com 30 dias para este CPF/CNPJ.\\n\\n"
                    f"⏱ _{tempo_decorrido}s_",
                )
            else:"""

WEBHOOK_REPLACEMENT = """            if msg == "no_results" or not detalhes:
                legenda = (
                    "📡 *Status online (PAP)*\\n\\n"
                    "Não tem pedido com 30 dias para este CPF/CNPJ.\\n\\n"
                    f"⏱ _{tempo_decorrido}s_"
                )
                enviado_imagem = False
                if list_screenshot_path and os.path.isfile(list_screenshot_path):
                    try:
                        with open(list_screenshot_path, "rb") as f:
                            import base64
                            img_b64 = base64.b64encode(f.read()).decode("utf-8")
                        if whatsapp.enviar_imagem_b64(telefone, img_b64, caption=legenda):
                            enviado_imagem = True
                    except Exception as e_img:
                        logger.warning("[STATUS ONLINE] Erro ao enviar imagem sem resultado: %s", e_img)
                if not enviado_imagem:
                    whatsapp.enviar_mensagem_texto(telefone, legenda)
            else:"""

ZAPI_TARGET = """        resp = self._send_request(url, payload)
        if not resp or not isinstance(resp, dict):
            return None
        if resp.get("error"):
            return None
        if self.resposta_indica_sucesso(resp):
            return resp
        return None"""

ZAPI_REPLACEMENT = """        resp = self._send_request(url, payload)
        if not resp or not isinstance(resp, dict):
            logger.error("[Z-API] Falha ao enviar imagem. Resposta invalida: %s", resp)
            return None
        if resp.get("error"):
            logger.error("[Z-API] Falha ao enviar imagem. Erro da API: %s", resp)
            return None
        if self.resposta_indica_sucesso(resp):
            return resp
        logger.error("[Z-API] Falha ao enviar imagem. Nao indica sucesso: %s", resp)
        return None"""

EVO_TARGET = """        resp = self._request("POST", path, payload, timeout=60)
        if isinstance(resp, dict) and resp.get("error"):
            return None
        if resp and self.resposta_indica_sucesso(resp if isinstance(resp, dict) else {}):
            return self._normalize_success(resp)
        return None"""

EVO_REPLACEMENT = """        resp = self._request("POST", path, payload, timeout=60)
        if isinstance(resp, dict) and resp.get("error"):
            logger.error("[Evolution] Falha ao enviar imagem. Erro da API: %s", resp)
            return None
        if resp and self.resposta_indica_sucesso(resp if isinstance(resp, dict) else {}):
            return self._normalize_success(resp)
        logger.error("[Evolution] Falha ao enviar imagem. Resposta nao indica sucesso: %s", resp)
        return None"""

def fix_celery_py(project_dir):
    path = os.path.join(project_dir, "core_config", "celery.py")
    if not os.path.exists(path): return False
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("'core_config.settings'", "'gestao_equipes.settings'")
    content = content.replace("Celery('core_config')", "Celery('gestao_equipes')")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def fix_settings_py(project_dir):
    path = os.path.join(project_dir, "gestao_equipes", "settings.py")
    if not os.path.exists(path): return False
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if "CELERY_BROKER_URL" not in content:
        content += "\\n" + CELERY_CONFIG
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

def replace_in_file(project_dir, subpath, target, replacement):
    path = os.path.join(project_dir, subpath)
    if not os.path.exists(path): return False
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if target in content:
        content = content.replace(target, replacement)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

def main():
    for proj in PROJECTS:
        print(f"\\nProcessing {proj}...")
        proj_dir = os.path.join(BASE_DIR, proj)
        if not os.path.isdir(proj_dir):
            print(f"Directory not found: {proj_dir}")
            continue
            
        fix_celery_py(proj_dir)
        fix_settings_py(proj_dir)
        replace_in_file(proj_dir, r"crm_app\\whatsapp_webhook_handler.py", WEBHOOK_TARGET, WEBHOOK_REPLACEMENT)
        replace_in_file(proj_dir, r"crm_app\\services\\whatsapp\\zapi_provider.py", ZAPI_TARGET, ZAPI_REPLACEMENT)
        replace_in_file(proj_dir, r"crm_app\\services\\whatsapp\\evolution_provider.py", EVO_TARGET, EVO_REPLACEMENT)
        
        # Git commit and push
        print(f"Committing and pushing {proj}...")
        subprocess.run(["git", "add", "."], cwd=proj_dir)
        subprocess.run(["git", "commit", "-m", "fix: envia print no_results, adiciona logs ZAPI/Evolution e corrige Celery"], cwd=proj_dir)
        subprocess.run(["git", "push"], cwd=proj_dir)
        print(f"Done {proj}")

if __name__ == "__main__":
    main()
