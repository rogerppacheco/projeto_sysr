"""Aplica nos sites o patch de Celery, print de no_results e logs ZAPI/Evolution.

Uso:
    python apply_fixes.py --dry-run          # mostra o diff, não grava nada
    python apply_fixes.py --no-push          # grava e commita, sem push
    python apply_fixes.py                    # grava, commita e faz push
    python apply_fixes.py --projects site-gm site-bn
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from patch_utils import PatchError, SourceFile, commit_files, ensure_clean_worktree

PROJECTS = [
    "site-rosso",
    "site-clickup",
    "site-gm",
    "site-bn",
    "nova-velox",
]

BASE_DIR = Path(__file__).resolve().parent

COMMIT_MESSAGE = "fix: envia print no_results, adiciona logs ZAPI/Evolution e corrige Celery"

CELERY_CONFIG = """
# Configurações do Celery
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
"""

# Nos trechos abaixo, "\\n" é intencional: vira o escape \n dentro do código Python de destino.
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

CELERY_PY_REPLACEMENTS = [
    (Path("core_config", "celery.py"), "'core_config.settings'", "'gestao_equipes.settings'"),
    (Path("core_config", "celery.py"), "Celery('core_config')", "Celery('gestao_equipes')"),
]

REPLACEMENTS = [
    (Path("crm_app", "whatsapp_webhook_handler.py"), WEBHOOK_TARGET, WEBHOOK_REPLACEMENT),
    (Path("crm_app", "services", "whatsapp", "zapi_provider.py"), ZAPI_TARGET, ZAPI_REPLACEMENT),
    (Path("crm_app", "services", "whatsapp", "evolution_provider.py"), EVO_TARGET, EVO_REPLACEMENT),
]


def django_settings_module(proj_dir: Path) -> str | None:
    match = re.search(
        r"setdefault\(\s*['\"]DJANGO_SETTINGS_MODULE['\"]\s*,\s*['\"]([\w.]+)['\"]",
        (proj_dir / "manage.py").read_text(encoding="utf-8"),
    )
    return match.group(1) if match else None


def build_patches(proj_dir: Path) -> dict[Path, SourceFile]:
    files: dict[Path, SourceFile] = {}

    def get(rel: Path) -> SourceFile | None:
        path = proj_dir / rel
        if not path.is_file():
            print(f"  [AVISO] arquivo não existe: {rel}")
            return None
        if rel not in files:
            files[rel] = SourceFile.load(path)
        return files[rel]

    replacements = list(REPLACEMENTS)
    settings_module = django_settings_module(proj_dir)
    if settings_module == "gestao_equipes.settings":
        replacements = CELERY_PY_REPLACEMENTS + replacements
    else:
        print(f"  [AVISO] manage.py usa {settings_module}; core_config/celery.py não será alterado")

    for rel, target, replacement in replacements:
        src = get(rel)
        if src is None:
            continue
        status = src.replace_once(target, replacement)
        if status == "nao_encontrado":
            print(f"  [AVISO] trecho não encontrado em {rel}; pulando")

    settings = get(Path("gestao_equipes", "settings.py"))
    if settings is not None and "CELERY_BROKER_URL" not in settings.text:
        settings.append_block(CELERY_CONFIG)

    return {rel: src for rel, src in files.items() if src.changed}


def process_project(proj: str, dry_run: bool, push: bool) -> bool:
    print(f"\n=== {proj}")
    proj_dir = BASE_DIR / proj
    if not proj_dir.is_dir():
        print(f"  [ERRO] diretório não encontrado: {proj_dir}")
        return False

    try:
        ensure_clean_worktree(proj_dir)
        changed = build_patches(proj_dir)
        if not changed:
            print("  Nada a alterar (patch já aplicado).")
            return True

        for src in changed.values():
            src.validate()

        if dry_run:
            for src in changed.values():
                print(src.diff())
            return True

        for src in changed.values():
            src.save()
            print(f"  gravado: {src.path.relative_to(proj_dir)}")

        commit_files(proj_dir, [src.path for src in changed.values()], COMMIT_MESSAGE, push=push)
        print("  commit" + (" e push" if push else "") + " concluídos")
        return True
    except PatchError as exc:
        print(f"  [ERRO] {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="mostra o diff sem gravar nada")
    parser.add_argument("--no-push", action="store_true", help="commita mas não faz push")
    parser.add_argument("--projects", nargs="+", default=PROJECTS, metavar="PROJETO")
    args = parser.parse_args()

    failures = [p for p in args.projects if not process_project(p, args.dry_run, push=not args.no_push)]
    if failures:
        print(f"\nFalhou em: {', '.join(failures)}")
        return 1
    print("\nConcluído sem erros.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
