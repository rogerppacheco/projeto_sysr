with open(r'c:\Projeto_Sysr\nova-velox\core_config\settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """    'lista_agendamento_vendedor_tarde': {
        'task': 'crm_app.tasks_celery.run_legacy_scheduler_job',
        'schedule': crontab(minute='30', hour='12'),
        'args': ('lista_agendamento_vendedor_tarde',)
    }
}"""

new = """    'lista_agendamento_vendedor_tarde': {
        'task': 'crm_app.tasks_celery.run_legacy_scheduler_job',
        'schedule': crontab(minute='30', hour='12'),
        'args': ('lista_agendamento_vendedor_tarde',)
    },
    'varrer_jobs_pendentes_pap': {
        'task': 'crm_app.tasks_celery.varrer_jobs_pendentes_pap',
        'schedule': 15.0,  # A cada 15 segundos
    },
}"""

if old in content:
    content = content.replace(old, new)
    with open(r'c:\Projeto_Sysr\nova-velox\core_config\settings.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK - nova-velox settings.py atualizado!")
else:
    old_rn = old.replace('\n', '\r\n')
    new_rn = new.replace('\n', '\r\n')
    if old_rn in content:
        content = content.replace(old_rn, new_rn)
        with open(r'c:\Projeto_Sysr\nova-velox\core_config\settings.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("OK - nova-velox settings.py atualizado (CRLF)!")
    else:
        print("ERRO - padrão não encontrado!")
