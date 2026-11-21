---
name: whatsapp-engineer
description: Instalar e configurar o WhatsApp Engineer V2 por uma conversa guiada em português, conectando vários telefones por QR, registrando número, pessoa e setor, importando histórico e ativando sincronizações programadas. Usar também para consultar mensagens por pessoa ou setor e verificar a situação dos telefones.
---

# WhatsApp Engineer V2

Conduza a instalação na conversa. Execute os comandos técnicos com suas ferramentas e apresente à pessoa somente as decisões, o progresso e as instruções para usar o celular. Use `scripts/onboard.py` como entrada da V2. Leia [operação](references/operacao-v2.md) para os comandos e [ambientes](references/ambientes-v2.md) para registrar a skill e as consultas no agente.

## Começar e preparar

Se o pacote ainda está na pasta extraída ou no checkout temporário, siga `INICIAR.md`. Use o diretório estável devolvido pelo instalador. Reconheça o agente e o ambiente pela sessão atual. Aproveite informações que a pessoa já forneceu.

Abra a conversa assim, ajustando ao que já for conhecido.

> Vou preparar o acompanhamento dos seus WhatsApps. Preciso do número com DDD, do nome de quem usa e do setor de cada telefone. Depois vamos combinar os horários de sincronização e conectar os celulares.
>
> Separe os celulares que vamos conectar. Vou mostrar um código QR para cada aparelho quando você estiver pronto.

Rode `doctor` e `prepare`. Se faltarem Python 3.10+ ou Node.js com `node:sqlite` (22.13+), instale pelo gerenciador oficial disponível conforme a autorização e as permissões do ambiente. Descubra os caminhos executáveis. Uma falha técnica deve ser explicada com o próximo passo concreto.

## Cadastrar os telefones

Pergunte tudo de uma vez para reduzir idas e voltas.

> Quais telefones vamos acompanhar? Para cada um, me passe o número com DDD, quem usa e o setor.
>
> Por exemplo, (11) 90000-0001, Ana Souza, Vendas. Isso permite pedir depois uma análise das conversas da Ana ou do setor de Vendas.

Pergunte somente o campo que estiver faltando. Telefones compartilhados podem ter uma equipe identificada como usuária. Para números de outro país, confirme o código do país. Os exemplos do pacote são fictícios e precisam ser substituídos pelas respostas da pessoa.

Explique e confirme a autorização, aproveitando a finalidade já descrita.

> Essa conexão traz para o servidor o histórico que o WhatsApp disponibilizar, inclusive conversas pessoais que existirem nesses números. Os responsáveis autorizaram conectar os telefones para esse acompanhamento?

Registre autorização explícita por telefone. O cadastro preserva número, pessoa e setor como campos próprios. Use esses campos para escolher os bancos ao responder a uma análise. Aplique as permissões do agente à consulta e à divulgação. Pergunte quem pode receber as análises somente se essa informação fizer falta para o uso solicitado.

## Explicar e escolher os horários de sincronização

Apresente o padrão recomendado de uma vez.

> Recomendo sincronizar as conversas a cada duas horas, todos os dias, das 06h às 22h, no horário de Brasília. Sincronizar o tempo todo pode sobrecarregar o servidor.
>
> Você pode pedir uma análise a qualquer hora. Ela usa as conversas que já foram copiadas. Por exemplo, se a última sincronização foi às 08h e você pedir às 09h30, as mensagens mais recentes podem aparecer só a partir da rodada das 10h.
>
> Posso usar esses horários ou você prefere outros?

Quando couber, acrescente “A primeira cópia começa assim que conectarmos o telefone. A última rodada começa às 22h e pode levar até 45 minutos.” Os horários indicam os inícios das sincronizações.

O padrão segue a rotina do Iago, com verificações a cada 120 segundos, comparação de duas amostras e encerramento coletivo quando cada telefone conectado apresenta aumento de até 19 registros entre as medições. Cada rodada tem limite de 45 minutos ou 24 medições. Esses parâmetros já vêm configurados. Explique somente se a pessoa perguntar.

Para personalizar, peça hora inicial, último início, intervalo, dias e cidade/fuso somente quando ainda desconhecidos. O comando de configuração aceita horas inteiras e intervalos de 1, 2, 4, 6 ou 12 horas. Traduza a escolha para o JSON do agente. Salve com `configure` e apresente os horários escolhidos em português.

## Preparar o celular e gerar o QR

Conecte um telefone por vez, identificado pelo número, pessoa e setor. Consulte `status` antes de gerar código para reaproveitar sessões válidas.

> Vamos conectar o telefone da Ana, de Vendas, número final 0001. Deixe esse celular desbloqueado e abra esta conversa em outra tela, como a do computador.
>
> No celular, abra o WhatsApp, entre em Aparelhos conectados e toque em Conectar aparelho. Quando a câmera estiver aberta, me avise para eu mostrar o código QR.

Aguarde essa resposta antes de executar `pair --ready`. O comando inicia a engine própria desse telefone e devolve o caminho do QR quando ele está atual. Entregue imediatamente a imagem pela ferramenta de anexos da conversa privada autorizada. Use a capacidade real de mídia do agente. No OpenClaw, a linha `MEDIA:/caminho/absoluto/qr.png` é um fallback quando suportado pelo canal. Para Codex ou Claude local, use a exibição de imagem disponível. Se o agente estiver sendo instalado por um grupo, resolva uma conversa privada com o operador antes de gerar o QR.

> Código pronto. Aponte a câmera do WhatsApp desse celular para a imagem.

Mantenha o processo ativo enquanto a pessoa escaneia. Reconsulte `status` para conferir a conexão e `number_matches`. Se o código expirar, explique “O código venceu. Está com a câmera do celular pronta para eu mostrar outro?”. Um código atualizado pode aparecer enquanto a engine aguarda. `status` só anuncia códigos com menos de 45 segundos. Use a imagem atual, após confirmar a prontidão.

Se a identidade divergir do cadastro, pare somente esse perfil e esclareça qual telefone a pessoa está conectando. Se houver logout confirmado, siga a recuperação assistida em `references/operacao-v2.md`, que preserva o banco e a autenticação anterior. Evite reinícios repetidos para o mesmo erro.

Quando confirmar, diga “Telefone da Ana conectado. Já comecei a receber o histórico disponível.” Repita o procedimento com o próximo aparelho.

## Primeira sincronização e consulta

Os workers começam a copiar o histórico ao conectar. Após o pareamento, execute `sync --background`. Acompanhe `status` e o arquivo `last-cycle.json` em intervalos adequados. A rodada prossegue em processo próprio enquanto você conduz a conversa.

> Estou trazendo as conversas e conferindo a primeira cópia. Vou guardar o que já chegar e avisar se precisar continuar na próxima rodada.

Use contadores e período encontrado para informar o progresso. A primeira rodada encerra por estabilização observada, limite ou falha. O resultado inclui saúde observada de cada conexão e o motivo de parada. Crescimento baixo com conexão falha exige atenção. Descreva o histórico como “histórico disponibilizado pelo WhatsApp”, com o período encontrado. A primeira rodada poderá ficar parcial, e os próximos horários poderão continuar recebendo dados.

Confirme uma consulta limitada com `search`. Ela usa os mesmos bancos dos workers. Quando o agente já oferece MCP local, obtenha o descritor com `mcp` e registre pelo mecanismo do ambiente. O comando de busca direta também permite concluir as consultas dentro desta skill quando o MCP estiver indisponível.

## Ativar e conferir a rotina

Execute `schedule` para gerar a configuração e `schedule --install` para ativá-la. Em Linux, confira `survives_logout`. Se estiver falso, habilite a permanência do serviço do usuário com `loginctl enable-linger` quando as permissões e o escopo permitirem. Se precisar de administrador, explique a pendência específica. Em Mac, a rotina requer computador ligado e usuário conectado. Preserve outros serviços e números usados pelo canal de comunicação do agente.

Confira `status` após a ativação e informe a próxima sincronização com data, hora e fuso. Verifique conexão, consulta e agendamento como etapas de conclusão. Quando a primeira rodada ficar parcial, descreva o que já está disponível e quando continuará.

Exemplo de conclusão, preenchido com as evidências da instalação.

> O telefone da Ana, de Vendas, e o do Bruno, de Atendimento, estão conectados. A primeira cópia encontrou conversas de [período]. As sincronizações estão programadas para [horários]. A próxima será [data e hora].
>
> Agora você pode pedir uma análise por pessoa ou setor. Em cada resposta, vou informar quando as conversas foram sincronizadas.

Para consultas futuras, selecione os perfis por `person` e `department`, limite o período, use `search` ou MCP e informe a última rodada conhecida. Perguntas que incluem horas posteriores à última sincronização precisam indicar que pode haver mensagens ainda pendentes de cópia.
