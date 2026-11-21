# WhatsApp Engineer V2

Instale o acompanhamento de vários números de WhatsApp por uma conversa guiada em português. O agente pede número, nome de quem usa e setor, explica os horários de sincronização, apresenta os códigos QR e configura a rotina.

## Copie e cole no seu agente

```text
Instale o WhatsApp Engineer V2 usando o repositório abaixo e me guie em português até deixar a configuração pronta.

https://github.com/spanevello0x/whatsapp-engineer-v2

Leia INICIAR.md e SKILL.md e siga o roteiro. Execute a preparação técnica com suas ferramentas. Me peça número com DDD, nome de quem usa e setor de cada telefone. Explique os horários recomendados de sincronização e que as conversas recentes podem aguardar a próxima rodada. Antes de gerar cada código QR, espere eu confirmar que o celular está pronto. Acompanhe a primeira sincronização, ative os horários e informe o resultado de cada telefone e a próxima execução.
```

Você também pode entregar o [ZIP da versão 2.0.0](https://github.com/spanevello0x/whatsapp-engineer-v2/releases/download/v2.0.0/whatsapp-engineer-v2-2.0.0.zip) ao agente e enviar o mesmo pedido, indicando o arquivo anexado. O agente precisa conseguir ler e extrair o arquivo.

## Durante a configuração

Tenha os celulares disponíveis e o WhatsApp aberto. O agente vai pedir, para cada telefone, o número com DDD, o nome de quem utiliza e o setor. Por exemplo, telefone da Ana Souza, do setor de Vendas. Isso ajuda em análises posteriores por pessoa ou equipe.

A recomendação é sincronizar a cada duas horas, todos os dias, das 06h às 22h, no horário de Brasília. Você pode escolher outros horários. As análises usam as conversas já copiadas. Se a última sincronização foi às 08h, mensagens recebidas depois podem aparecer só a partir da rodada das 10h. Sincronizar continuamente pode sobrecarregar o servidor.

A primeira cópia começa após conectar cada telefone. O agente acompanha o progresso, preserva o que já chegou e informa quando uma continuação for necessária.

## Onde instalar

O serviço de sincronização funciona em uma VPS Linux com systemd ou em um Mac que permaneça ligado e com usuário conectado nos horários escolhidos. Hermes e OpenClaw na VPS podem usar a própria máquina. Codex e Claude Code podem preparar uma instalação local ou por SSH em uma VPS. Uma conversa na nuvem precisa ter acesso ao ambiente onde o serviço ficará rodando.

O pacote inclui o mesmo roteiro para esses agentes. O instalador adapta o diretório da skill. A entrega de QR e o registro opcional do MCP usam as capacidades disponíveis no ambiente. O agente identifica essas condições durante a configuração. Consulte [os detalhes dos ambientes](references/ambientes-v2.md).

## Para quem instala manualmente

Clone ou extraia o pacote completo, leia `INICIAR.md` e escolha o agente.

```bash
git clone https://github.com/spanevello0x/whatsapp-engineer-v2.git
cd whatsapp-engineer-v2
python3 install.py --agent hermes
```

O comando imprime a pasta estável da instalação. Peça ao agente para ler `SKILL.md` nessa pasta e seguir o roteiro. O agente executa preparação, cadastro, conexão, sincronização e agendamento pelos [comandos de operação](references/operacao-v2.md).

## Versão e origem

A V2 usa a engine Baileys e os buscadores da base pública [WhatsApp Engineer](https://github.com/spanevello0x/whatsapp-engineer), commit `b7df832e7c3ad6682ffef3105bf40d6bb3941830`. Ela acrescenta instalação guiada e a coordenação de telefones e ciclos inspirada na operação do Iago. Cada telefone mantém autenticação, banco e mídia separados.

O pacote foi conferido quanto a estrutura, sintaxe, cadastro fictício e geração dos agendamentos. O QR e a captura são verificados durante a instalação com o telefone do usuário. O histórico disponível depende do que o WhatsApp fornece. A versão 2.0.0 preserva os arquivos da engine original.

Os dados ficam em `~/.local/share/whatsapp-engineer`, fora do repositório. Banco, mídia, QR e autenticação são privados. A engine de captura deve ter sua própria sessão por telefone. O uso das conversas segue a autorização dos responsáveis e as permissões do agente que faz as consultas.

Licença MIT, com a atribuição da base preservada em `LICENSE`.
