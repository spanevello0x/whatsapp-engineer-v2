# Iniciar a instalação guiada

Você recebeu este repositório ou ZIP para instalar o WhatsApp Engineer V2 e conduzir uma pessoa leiga até a configuração completa.

1. Leia `SKILL.md` na íntegra e siga seu roteiro. Conduza a conversa em português, com mensagens curtas e uma decisão por vez.
2. Verifique o ambiente com as ferramentas que você já possui. Descubra qual agente está executando esta conversa e se há um servidor ou computador persistente disponível. Use a máquina do próprio agente quando ela já oferece execução e armazenamento persistentes.
3. Trabalhe com o pacote completo. Ao receber o link, clone o repositório inteiro. Ao receber o ZIP, extraia-o e encontre esta pasta. Os arquivos `package.json`, `package-lock.json`, `workspace/baileys_worker.mjs` e `scripts/` precisam acompanhar a skill.
4. Execute `python3 install.py --agent hermes`, `openclaw`, `codex`, `claude` ou `other`, conforme o ambiente. O comando imprime o destino estável. Passe a usar os scripts desse destino nas próximas etapas.
5. Siga `SKILL.md` a partir da preparação. A pessoa só precisa responder sobre seus telefones, entender os horários e escanear os códigos. Resolva caminhos, programas, pastas e agendamento com as ferramentas disponíveis.

Uma pessoa pode enviar somente o link acompanhado de “instale e me guie”. Essa mensagem autoriza preparar o pacote e conduzir o roteiro. A conexão de cada telefone depende da autorização do responsável e da presença da pessoa para ler o QR.

## Ambientes de execução

A sincronização deste pacote roda em Linux com systemd ou macOS com launchd. O serviço guarda autenticação, mensagens e mídias no ambiente de instalação. Hermes e OpenClaw na VPS usam essa própria máquina. Claude Code e Codex podem instalar localmente ou conduzir o preparo em uma VPS por SSH.

Quando a conversa acontece em um ambiente temporário, descubra um servidor persistente já disponível. Se a informação realmente faltar, explique “Preciso de um computador ou servidor que continue ligado para buscar as conversas nos horários combinados. Qual vamos usar?”. Continue a preparação independente dessa resposta e aguarde o acesso necessário para instalar o serviço. No Windows, use uma VPS Linux ou um Linux com systemd previamente disponível.

## Conclusão da instalação

O trabalho termina quando cada telefone tem número, pessoa e setor registrados, a conexão foi conferida, a primeira rodada tem resultado conhecido, as consultas estão disponíveis e o agendamento está ativo com a próxima execução identificada. Informe uma pendência específica quando algum desses passos precisar de continuação. O código QR precisa ser gerado e entregue durante a instalação real.
