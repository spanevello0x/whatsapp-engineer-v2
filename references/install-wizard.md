# Install Wizard

O `install-wizard` existe para transformar a WhatsApp Engineer em uma skill publicavel sem esconder o risco real do pareamento.

## Objetivo

Conduzir qualquer instalador, em OpenClaw, Hermes, Codex ou outro runtime, ate um plano seguro de instalacao:

1. explicar que o pareamento pode baixar 100% das conversas acessiveis pelo WhatsApp Web;
2. exigir confirmacao de entendimento antes do QR real;
3. registrar telefones, donos, finalidade, escopo, consentimento e cadencia;
4. preparar o QR como imagem pronta para envio pelo gateway escolhido;
5. sugerir rotina de monitoramento, cron e usabilidade;
6. salvar tudo fora do Git em `~/.openclaw/state/whatsapp-engineer/`.

## Comandos

Simular:

```bash
python3 workspace/run.py simulate-install --print-plan
```

Rodar wizard interativo:

```bash
python3 workspace/run.py install-wizard
```

Gerar QR e monitorar:

```bash
python3 workspace/run.py install-wizard --generate-qr --monitor
```

Rodar com respostas JSON:

```bash
python3 workspace/run.py install-wizard --answers answers.json --print-plan
```

## Avisos que o wizard precisa preservar

- O historico pode ser baixado integralmente para SQLite local.
- Bancos, midias, logs, QR e sessoes nunca entram no Git.
- O agente consumidor precisa impedir vazamento de conversa bruta.
- Publicacao em grupo/canal precisa de destino confirmado e guardrail.
- Sincronia continua so deve ser usada quando tempo real for necessario.
- O dono de cada telefone precisa consentir.

## Arquivos gerados

```text
~/.openclaw/state/whatsapp-engineer/install/install-plan.json
~/.openclaw/state/whatsapp-engineer/install/qr-handoff.png
~/.openclaw/state/whatsapp-engineer/phone_registry.json
```

Esses arquivos sao privados do ambiente. Nao versionar.

## Cadencias sugeridas

- `continuous`: worker ativo para operacao critica; usar digest de controle a cada 15-30 min.
- `hourly`: resumo operacional por hora, bom padrao para suporte/vendas.
- `daily`: resumo executivo ou auditoria leve.
- `business-hours`: avisos de pendencia durante horario comercial.
- `manual`: uso sob demanda em ambiente sensivel ou fase de teste.

## Gateway do QR

O wizard nao assume um provedor unico. Ele prepara uma imagem e imprime uma das rotas:

- `MEDIA:/path/to/qr-handoff.png` para agentes que entendem entrega por midia;
- caminho do arquivo para anexo manual;
- comando custom com `{path}` e `{message}` para gateways proprios.

O operador deve enviar o QR imediatamente. QR antigo deve ser descartado.
