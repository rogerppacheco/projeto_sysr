import os

sites = ['site-bn', 'site-clickup', 'site-gm', 'site-record', 'site-rosso']
for site in sites:
    filepath = f"c:/Projeto_Sysr/{site}/core/templates/governanca.html"
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'operadora_usa_pap_nio' not in content:
        # Patch the form HTML
        old_form = '<div class="col-md-3"><label class="form-label fw-bold">Status</label><select id="operadora_status" class="form-select" required><option value="1">Ativo</option><option value="0">Inativo</option></select></div><div class="col-md-2"><button type="submit" class="btn btn-primary w-100">Salvar</button></div></form><table class="table table-hover align-middle">'
        new_form = '<div class="col-md-2"><label class="form-label fw-bold">Status</label><select id="operadora_status" class="form-select" required><option value="1">Ativo</option><option value="0">Inativo</option></select></div><div class="col-md-2"><label class="form-label fw-bold">Portal PAP</label><select id="operadora_usa_pap_nio" class="form-select" required title="Marque Sim somente para a Nio. O portal PAP não consulta pedidos de Vero, Velox e demais operadoras."><option value="0" selected>Não</option><option value="1">Sim (só Nio)</option></select></div><div class="col-md-2"><button type="submit" class="btn btn-primary w-100">Salvar</button></div></form><p class="small text-muted mb-3">O <strong>Portal PAP</strong> só faz sentido para a operadora <strong>Nio</strong>. Com "Não", a automação de status da Esteira e as demais consultas PAP ignoram as vendas dessa operadora.</p><table class="table table-hover align-middle">'
        content = content.replace(old_form, new_form)
        
        # Patch table header
        old_thead = '<thead class="table-light"><tr><th>Nome</th><th>CNPJ</th><th>Status</th><th>Ações</th></tr></thead>'
        new_thead = '<thead class="table-light"><tr><th>Nome</th><th>CNPJ</th><th>Status</th><th>Portal PAP</th><th>Ações</th></tr></thead>'
        content = content.replace(old_thead, new_thead)
        
        # Patch JS for table rendering
        old_js_render = "const badgeAtivo = o.ativo ? '<span class=\"badge bg-success\">Ativo</span>' : '<span class=\"badge bg-danger\">Inativo</span>';"
        new_js_render = "const badgeAtivo = o.ativo ? '<span class=\"badge bg-success\">Ativo</span>' : '<span class=\"badge bg-danger\">Inativo</span>';\n                const badgePap = o.usa_pap_nio ? '<span class=\"badge bg-success\">Sim</span>' : '<span class=\"badge bg-secondary\">Não</span>';"
        content = content.replace(old_js_render, new_js_render)
        
        old_js_row = "<td>${badgeAtivo}</td>\n                        <td>\n                            <button class=\"btn btn-sm btn-info text-white me-1\""
        new_js_row = "<td>${badgeAtivo}</td>\n                        <td>${badgePap}</td>\n                        <td>\n                            <button class=\"btn btn-sm btn-info text-white me-1\""
        content = content.replace(old_js_row, new_js_row)
        
        # Patch JS save function
        old_js_save = "const body = { nome: document.getElementById('operadora_nome').value, cnpj: document.getElementById('operadora_cnpj').value, ativo: document.getElementById('operadora_status').value == '1' };"
        new_js_save = "const body = { nome: document.getElementById('operadora_nome').value, cnpj: document.getElementById('operadora_cnpj').value, ativo: document.getElementById('operadora_status').value == '1', usa_pap_nio: document.getElementById('operadora_usa_pap_nio').value == '1' };"
        content = content.replace(old_js_save, new_js_save)
        
        # Patch JS edit function
        old_js_edit = "document.getElementById('operadora_status').value = o.ativo ? '1' : '0'; };"
        new_js_edit = "document.getElementById('operadora_status').value = o.ativo ? '1' : '0'; document.getElementById('operadora_usa_pap_nio').value = (o.usa_pap_nio === false) ? '0' : '1'; };"
        content = content.replace(old_js_edit, new_js_edit)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # git commit and push
        os.system(f'cd c:/Projeto_Sysr/{site} && git add core/templates/governanca.html && git commit -m "feat(ui): add usa_pap_nio field to Operadora form" && git push origin main')
        print(f"Patched {site}")
    else:
        print(f"Already patched {site}")
