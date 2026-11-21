# Comandos da instalação V2

Execute no diretório estável devolvido por `install.py`. Estes comandos são para o agente. Apresente as perguntas de `SKILL.md` à pessoa.

## Preparação

```bash
python3 scripts/onboard.py doctor
python3 scripts/onboard.py prepare
```

`doctor` confere caminhos e suporte ao SQLite do Node. `prepare` instala as dependências do lockfile com `npm ci --omit=dev` e guarda o caminho absoluto do Node. A engine continua sendo o arquivo herdado da base pública. Áudio e OCR usam as dependências já presentes nessa base.

## Cadastro

Grave as respostas em um arquivo privado fora do repositório ou envie o JSON pela entrada padrão. Exemplo fictício, a substituir pelos dados coletados e pela autorização real.

```bash
python3 scripts/onboard.py configure --answers - <<'JSON'
{
  "purpose": "Acompanhar atendimentos e pendências",
  "phones": [
    {
      "number": "+5511900000001",
      "person": "Ana Souza",
      "department": "Vendas",
      "consent": true
    }
  ]
}
JSON
```

O padrão já inclui o fuso de Brasília, nove rodadas por dia, de 06h a 22h, a cada duas horas. Para uma escolha diferente, inclua `sync` no mesmo JSON.

```json
{
  "sync": {
    "timezone": "America/Sao_Paulo",
    "start_hour": 8,
    "end_hour": 18,
    "every_hours": 2,
    "weekdays_only": true
  }
}
```

Use horas inteiras. Uma janela até 18h significa que a última rodada começa nesse horário. Campos internos de proteção são `check_seconds=120`, `max_delta=19`, `max_minutes=45` e `max_samples=24`.

A configuração faz atualização por número e preserva os perfis existentes que não estiverem no novo envio. O identificador é `phone-` seguido do número internacional. Pessoa e setor podem ser atualizados sem mover o banco. Cada telefone tem autenticação, banco, mídia, QR e processo próprios.

## Pareamento

```bash
python3 scripts/onboard.py status
python3 scripts/onboard.py pair --profile phone-5511900000001 --ready
python3 scripts/onboard.py status --profile phone-5511900000001
```

Use `--ready` depois que a pessoa confirmar que está com a câmera do WhatsApp aberta. A saída `qr.fresh=true` acompanha o caminho atual da imagem. Entregue pelo recurso de mídia da conversa privada. Uma imagem de QR vencida precisa ser substituída pela atual. Conexões válidas podem ser reutilizadas.

`healthy_observed=true` combina processo próprio em execução, último evento de conexão aberto, número correspondente e banco legível. O arquivo de estado e o log da geração atual fornecem observações distintas. Um evento de histórico não apaga a informação do último fechamento.

Para encerrar um perfil durante o pareamento, use o comando abaixo. Ele identifica o processo pela assinatura salva e encerra somente a instância gerenciada.

```bash
python3 scripts/onboard.py stop --profile phone-5511900000001
```

Quando um logout foi diagnosticado e a pessoa confirmou a necessidade de reconectar, preserve a autenticação anterior e refaça o pareamento.

```bash
python3 scripts/onboard.py repair-auth --profile phone-5511900000001 --confirmed
python3 scripts/onboard.py pair --profile phone-5511900000001 --ready
```

`repair-auth` move a autenticação para uma pasta privada de backup e preserva banco e mídias. Identidade divergente requer esclarecer o cadastro antes de uma nova conexão. Confirme também que o número pertence a esta captura e que outra engine não usa a mesma autenticação.

## Primeira rodada e rotina

```bash
python3 scripts/onboard.py sync --background
python3 scripts/onboard.py status
```

`sync --background` acompanha os perfis habilitados em processo próprio e retorna o caminho de progresso. A engine já começa a importar após o pareamento. A rodada inclui os processos já conectados e os encerra ao finalizar, como na rotina de referência do Iago. O mesmo comando aceita `--profile` para uma seleção. Sem `--background`, a chamada acompanha a rodada em primeiro plano, como no serviço agendado.

O lock global coordena pareamento, operações manuais e ciclos deste pacote. Uma tentativa simultânea devolve uma mensagem para aguardar. Os resultados ficam em `last-cycle.json` e em `cycles/`, com contagens, situação de conexão e motivo de parada.

Uma rodada estabilizada requer duas amostras com conexão observada saudável para todos os perfis e crescimento entre 0 e 19 registros por perfil. Limite de duração, limite de medições, identidade divergente e erro de conexão são motivos próprios. O retorno `ok` descreve a rodada. A cobertura do histórico depende do que o WhatsApp entregou e do período encontrado no banco. A engine herdada não fornece um indicador confiável de conclusão integral de todos os lotes.

## Horários

```bash
python3 scripts/onboard.py schedule
python3 scripts/onboard.py schedule --install
python3 scripts/onboard.py status
```

A primeira chamada imprime a definição. A segunda instala um timer de usuário no Linux ou um LaunchAgent no Mac. No Linux, há um limite externo de 50 minutos no serviço, além do limite normal de 45 minutos do ciclo. O timer usa fuso explícito e `Persistent=false`, preservando o comportamento de aguardar o próximo horário se o servidor estava desligado.

Em Linux, se `survives_logout=false`, prepare a permanência do serviço do usuário quando autorizado e permitido.

```bash
loginctl enable-linger "$USER"
```

Quando o comando exigir administração, use o acesso administrativo já autorizado ou informe a pendência. O agendamento deve ficar ativo após a configuração, e `NextElapseUSecRealtime` deve indicar a próxima execução.

Em macOS, a sessão do usuário precisa estar conectada. O calendário usa o fuso do computador. O instalador verifica a diferença de horário atual e informa quando a escolha precisa ser ajustada. Para rotinas que precisem seguir outro fuso com mudanças sazonais, prefira o timer Linux com fuso explícito.

## Consulta

```bash
python3 scripts/onboard.py search --profile phone-5511900000001 --limit 10
python3 scripts/onboard.py search --profile phone-5511900000001 --after 2026-11-20T00:00:00-03:00 --limit 50
python3 scripts/onboard.py mcp
```

`search` usa o buscador da base original e o cadastro criado pela V2. Ele aceita `--query`, `--chat-name`, `--chat-jid`, `--after`, `--before`, `--limit` e `--page`. Descubra o identificador por pessoa e setor no cadastro. O descritor `mcp` aponta para o servidor local de consulta que já acompanha o pacote, com a variável `WHATSAPP_MCP_PROFILES_CONFIG` configurada.

O cadastro contém campos próprios `person` e `department`. O MCP herdado apresenta também `name` e `description` com pessoa e setor. Alguns indicadores do MCP são herdados da antiga bridge Go. Para saúde da engine V2, use `onboard.py status`. O download de mídia por MCP continua dependendo da bridge indicada pela implementação original. Mensagens e metadados de mídias já armazenadas podem ser consultados diretamente.

## Armazenamento e retomada

O padrão é `~/.local/share/whatsapp-engineer`. Defina `WHATSAPP_ENGINEER_HOME` antes de instalar para escolher outro local, mantendo a mesma variável nos comandos seguintes. O agendamento guarda essa localização.

- `app/` guarda o pacote instalado.
- `installation.json` guarda número, pessoa, setor, autorização e horários.
- `profiles.json` liga os workers às consultas.
- `profiles/<identificador>/` guarda os dados de cada telefone.
- `last-cycle.json` e `cycles/` guardam os resultados das rodadas.
- `auth-backups/` guarda autenticações preservadas em recuperações assistidas.

Releia a configuração e o status para retomar. Durante a retomada, aproveite as respostas já salvas e as conexões válidas. Se a primeira cópia ficou parcial, indique o que já foi encontrado e a próxima rodada.
