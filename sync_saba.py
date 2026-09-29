import os
import re

projects = [
    'nova-velox',
    'site-bn',
    'site-clickup',
    'site-gm',
    'site-record',
    'site-rosso'
]

def patch_file(filepath, old_str, new_str, skip_if_exists=None):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if skip_if_exists and skip_if_exists in content:
        print(f"Already patched: {filepath}")
        return

    if old_str not in content:
        print(f"Target string not found in: {filepath}")
        return

    content = content.replace(old_str, new_str)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched: {filepath}")

for p in projects:
    if p == 'nova-velox': 
        continue # Already did nova-velox manually
        
    base_dir = rf"c:\Projeto_Sysr\{p}"
    
    # 1. models.py
    models_path = os.path.join(base_dir, 'crm_app', 'models.py')
    old_model = '    pedido_pap = models.CharField(max_length=50, null=True, blank=True, unique=True, db_index=True, verbose_name="Pedido PAP")'
    new_model = '''    codigo_sa_ba = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Código SA/BA",
        help_text="Código identificador do contrato na Operadora (ex: SA-41538304, BA-...).",
    )
    pedido_pap = models.CharField(max_length=50, null=True, blank=True, unique=True, db_index=True, verbose_name="Pedido PAP")'''
    patch_file(models_path, old_model, new_model, skip_if_exists='codigo_sa_ba = models.CharField(')

    # 2. serializers.py
    ser_path = os.path.join(base_dir, 'crm_app', 'serializers.py')
    old_ser = "'complemento', 'bairro', 'cidade', 'estado',             'data_abertura', 'ordem_servico', 'data_agendamento',"
    new_ser = "'complemento', 'bairro', 'cidade', 'estado',             'data_abertura', 'ordem_servico', 'codigo_sa_ba', 'data_agendamento',"
    patch_file(ser_path, old_ser, new_ser, skip_if_exists="'codigo_sa_ba',")

    # 3. utils.py (montar_legenda)
    utils_path = os.path.join(base_dir, 'crm_app', 'utils.py')
    old_utils_1 = '    partes.append(f"• *Nº OS:* {d.get(\'numero_os\', \'\')}\\n")\n    if not d.get("nao_pertence_pdv"):'
    new_utils_1 = '''    if d.get("sa_ba_code"):
        partes.append(f"• *Nº OS:* {d.get('numero_os', '')} - {d.get('sa_ba_code')}\\n")
    else:
        partes.append(f"• *Nº OS:* {d.get('numero_os', '')}\\n")
    if not d.get("nao_pertence_pdv"):'''
    patch_file(utils_path, old_utils_1, new_utils_1, skip_if_exists='if d.get("sa_ba_code"):')

    # 4. utils.py (sincronizar_venda)
    old_utils_2 = '        sa_info = aplicar_status_agendamento_pap_na_venda(venda, d.get("status_agendamento"))\n        sa_nao_mapeado = sa_info.get("nao_mapeado")\n        salvou = False'
    new_utils_2 = '''        sa_info = aplicar_status_agendamento_pap_na_venda(venda, d.get("status_agendamento"))
        sa_nao_mapeado = sa_info.get("nao_mapeado")
        
        sa_ba_code = d.get("sa_ba_code")
        if sa_ba_code and venda.codigo_sa_ba != sa_ba_code:
            venda.codigo_sa_ba = sa_ba_code
            venda.save(update_fields=['codigo_sa_ba'])

        salvou = False'''
    patch_file(utils_path, old_utils_2, new_utils_2, skip_if_exists='venda.codigo_sa_ba = sa_ba_code')

    # 5. services_pap_nio.py (abrir_detalhe_os_e_extrair)
    srv_path = os.path.join(base_dir, 'crm_app', 'services_pap_nio.py')
    old_srv_1 = '''            # Pendência (ex.: "7029 - AGENDAMENTO DO PEDIDO") — rótulo exato, não "Pendência Cliente"
            pendencia_texto = self._buscar_pendencia_codigo_detalhe_pap()
            # Fallback: outros spans do detalhe
            if not status_agendamento or not agendamento_texto or not pendencia_texto:
                spans = self.page.locator(
                    'span.sc-jrOYZv.ldMRLh, span.ldMRLh, span.sc-gOhSNZ.fLfXPS'
                ).all()
                for s in spans:
                    t = (s.inner_text() or "").strip()
                    if not t:
                        continue
                    if re.match(r'\\d{2}/\\d{2}/\\d{4}\\s*-\\s*(Tarde|Manhã)', t) and not agendamento_texto:
                        agendamento_texto = t
                    if ("concluído" in t.lower() or "sucesso" in t.lower()) and not status_agendamento:
                        status_agendamento = t
                    if self._RE_PENDENCIA_CODIGO_PAP.match(t) and not pendencia_texto:
                        pendencia_texto = t
            if pendencia_texto and not self._RE_PENDENCIA_CODIGO_PAP.match(pendencia_texto):'''
    new_srv_1 = '''            # Pendência (ex.: "7029 - AGENDAMENTO DO PEDIDO") — rótulo exato, não "Pendência Cliente"
            pendencia_texto = self._buscar_pendencia_codigo_detalhe_pap()
            # SA/BA
            sa_ba_code = None
            try:
                spans_sa_ba = self.page.locator('span.sc-jrOYZv.ldMRLh, span.ldMRLh, span.sc-gOhSNZ.fLfXPS').all()
                for s in spans_sa_ba:
                    t = (s.inner_text() or "").strip()
                    if t and re.match(r"^(SA|BA)-\\d+$", t, re.I):
                        sa_ba_code = t
                        break
            except Exception:
                pass
            # Fallback: outros spans do detalhe
            if not status_agendamento or not agendamento_texto or not pendencia_texto or not sa_ba_code:
                spans = self.page.locator(
                    'span.sc-jrOYZv.ldMRLh, span.ldMRLh, span.sc-gOhSNZ.fLfXPS'
                ).all()
                for s in spans:
                    t = (s.inner_text() or "").strip()
                    if not t:
                        continue
                    if re.match(r'\\d{2}/\\d{2}/\\d{4}\\s*-\\s*(Tarde|Manhã)', t) and not agendamento_texto:
                        agendamento_texto = t
                    if ("concluído" in t.lower() or "sucesso" in t.lower()) and not status_agendamento:
                        status_agendamento = t
                    if self._RE_PENDENCIA_CODIGO_PAP.match(t) and not pendencia_texto:
                        pendencia_texto = t
                    if re.match(r"^(SA|BA)-\\d+$", t, re.I) and not sa_ba_code:
                        sa_ba_code = t
            if pendencia_texto and not self._RE_PENDENCIA_CODIGO_PAP.match(pendencia_texto):'''
    patch_file(srv_path, old_srv_1, new_srv_1, skip_if_exists='sa_ba_code = None')

    old_srv_2 = '''    def abrir_detalhe_os_e_extrair(
        self, numero_os: str, detalhe_href: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:'''
    new_srv_2 = '''    def abrir_detalhe_os_e_extrair(
        self, numero_os: str, detalhe_href: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:'''
    patch_file(srv_path, old_srv_2, new_srv_2, skip_if_exists='Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]')

    old_srv_3 = '''                self.page.wait_for_timeout(400)
            return (
                status_agendamento or None,
                agendamento_texto or None,
                pendencia_texto or None,
                detail_screenshot_path,
            )
        except Exception as e:
            logger.warning(f"[PAP] abrir_detalhe_os_e_extrair {numero_os}: {e}")
            try:
                self.page.go_back()
            except Exception:
                pass
            return None, None, None, None'''
    new_srv_3 = '''                self.page.wait_for_timeout(400)
            return (
                status_agendamento or None,
                agendamento_texto or None,
                pendencia_texto or None,
                sa_ba_code or None,
                detail_screenshot_path,
            )
        except Exception as e:
            logger.warning(f"[PAP] abrir_detalhe_os_e_extrair {numero_os}: {e}")
            try:
                self.page.go_back()
            except Exception:
                pass
            return None, None, None, None, None'''
    patch_file(srv_path, old_srv_3, new_srv_3, skip_if_exists='sa_ba_code or None')

    old_srv_4 = '''                st_ag, ag_texto, pendencia, detail_screenshot_path = self.abrir_detalhe_os_e_extrair(
                    num_os, detalhe_href=row.get("detalhe_href")
                )
                if st_ag is not None:
                    row["status_agendamento"] = st_ag
                if ag_texto is not None:
                    row["agendamento"] = ag_texto
                if pendencia is not None:
                    row["pendencia"] = pendencia
                if detail_screenshot_path:
                    row["detail_screenshot_path"] = detail_screenshot_path'''
    new_srv_4 = '''                st_ag, ag_texto, pendencia, sa_ba_code, detail_screenshot_path = self.abrir_detalhe_os_e_extrair(
                    num_os, detalhe_href=row.get("detalhe_href")
                )
                if st_ag is not None:
                    row["status_agendamento"] = st_ag
                if ag_texto is not None:
                    row["agendamento"] = ag_texto
                if pendencia is not None:
                    row["pendencia"] = pendencia
                if sa_ba_code is not None:
                    row["sa_ba_code"] = sa_ba_code
                if detail_screenshot_path:
                    row["detail_screenshot_path"] = detail_screenshot_path'''
    patch_file(srv_path, old_srv_4, new_srv_4, skip_if_exists='sa_ba_code, detail_screenshot_path = self.abrir_detalhe_os_e_extrair')

    # 6. esteira.html
    html_path = os.path.join(base_dir, 'core', 'templates', 'esteira.html')
    old_html = '''        function montarCelulaOsComStatusAgendamento(v) {
            const osAtual = v.ordem_servico || '-';
            const statusId = v.status_agendamento'''
    new_html = '''        function montarCelulaOsComStatusAgendamento(v) {
            const osAtual = v.codigo_sa_ba ? `${v.ordem_servico || '-'} - ${v.codigo_sa_ba}` : (v.ordem_servico || '-');
            const statusId = v.status_agendamento'''
    patch_file(html_path, old_html, new_html, skip_if_exists='v.codigo_sa_ba ?')
