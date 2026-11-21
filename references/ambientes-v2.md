# Instalação nos agentes

O pacote usa a mesma engine e os mesmos scripts em Linux ou macOS. A skill conduz a conversa usando as ferramentas de execução e de mídia oferecidas por cada agente.

## Pacote completo e registro

Use o repositório inteiro ou o ZIP da release. `install.py` copia o pacote para um diretório estável e registra um link para a skill.

| Agente | Comando do agente | Destino da skill |
| --- | --- | --- |
| Hermes | `python3 install.py --agent hermes` | `$HERMES_HOME/skills/whatsapp-engineer` ou `~/.hermes/skills/whatsapp-engineer` |
| OpenClaw | `python3 install.py --agent openclaw` | `$OPENCLAW_STATE_DIR/skills/whatsapp-engineer` ou `~/.openclaw/skills/whatsapp-engineer` |
| Codex local | `python3 install.py --agent codex` | `~/.agents/skills/whatsapp-engineer` |
| Claude Code local | `python3 install.py --agent claude` | `~/.claude/skills/whatsapp-engineer` |
| Outro agente com execução | `python3 install.py --agent other` | Caminho estável devolvido pelo comando, para leitura explícita |

A instalação copia os arquivos e orienta a leitura de `SKILL.md` na sessão atual. Se o agente exigir uma nova sessão para descobrir a skill automaticamente, a configuração atual pode prosseguir pela leitura explícita desse arquivo. Preserve uma skill anterior encontrada no destino e resolva a troca com base na instrução da pessoa e na situação atual.

Alguns instaladores de skills baixam somente `SKILL.md` e arquivos de apoio explicitamente referenciados. Este pacote precisa também da engine, do manifesto npm e do lockfile. Ao usar um hub, confira se todo o pacote veio junto. Clonar o repositório ou extrair o ZIP é o caminho direto.

## Execução persistente

Hermes e OpenClaw na VPS podem executar a sincronização nessa própria máquina. Codex e Claude Code locais podem executar no computador ou preparar a instalação na VPS por SSH. O terminal e o diretório de dados precisam pertencer ao ambiente que continuará sincronizando após o fim da conversa.

Em uma conversa hospedada sem execução persistente, prepare o serviço em uma máquina Linux acessível ao agente. A skill pode conduzir a instalação por SSH se essa ferramenta estiver disponível e autorizada. Consultas futuras podem usar SSH ou uma integração MCP já disponível. O MCP embutido neste pacote é local por stdio. Publicar um conector remoto exige uma configuração adicional de transporte e autenticação no ambiente escolhido.

Um arquivo arrastado para o chat precisa ficar acessível às ferramentas do agente. Se a interface tiver um fluxo próprio de instalação de skills, use esse fluxo para registrar a skill e mantenha o pacote executável no servidor persistente. O wizard orienta a pessoa quando houver alguma etapa da interface que só ela consiga concluir.

## Consultas e entrega do QR

O comando `python3 scripts/onboard.py mcp` fornece o descritor exato do servidor local. Use a configuração MCP suportada pela versão instalada do agente. Consulte a ajuda ou os arquivos atuais antes de gravar alterações e preserve servidores já configurados. Em Codex e Claude Code, use a CLI MCP quando disponível. Em Hermes e OpenClaw, use o registro MCP disponível naquele ambiente.

A busca direta por `scripts/onboard.py search` usa o mesmo cadastro e permite consultas mesmo sem registro MCP. A skill ensina a localizar o telefone pela pessoa ou pelo setor.

O caminho do QR é devolvido por `pair` ou `status` quando a imagem está atual. Envie como imagem pelo canal privado do operador. No Telegram, use a capacidade de anexos do agente. Em ferramentas locais, use a visualização de imagem do chat. Se o transporte só entregar arquivos, apresente o PNG como anexo e explique como abri-lo em outra tela para escanear com o celular.

## Compatibilidade desta distribuição

A engine vem do repositório `spanevello0x/whatsapp-engineer`, commit `b7df832e7c3ad6682ffef3105bf40d6bb3941830`. O motor e os buscadores herdados foram preservados. A V2 acrescenta a instalação estável, o roteiro de conversa e os comandos que organizam os perfis e o agendamento. A verificação do pacote cobre estrutura, sintaxe e configuração com dados fictícios. O pareamento é executado na instalação do usuário, com o aparelho autorizado disponível.
