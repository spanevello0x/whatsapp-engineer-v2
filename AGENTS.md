# WhatsApp Engineer V2

Quando este pacote for enviado para instalação, leia `INICIAR.md` e `SKILL.md` e conduza a configuração na conversa. O usuário é leigo. Resolva comandos, dependências, caminhos e agendamento com suas ferramentas. Peça número, pessoa e setor, explique a defasagem entre sincronizações e aguarde a prontidão do celular antes de gerar cada QR.

O código da engine em `workspace/baileys_worker.mjs` é herdado da base pública. A entrada de instalação da V2 fica em `scripts/onboard.py`. Os comandos antigos em `workspace/run.py` atendem compatibilidade da V1. Para instalar a V2, siga o fluxo de `SKILL.md`.

Na manutenção do pacote, confira sintaxe, referências e configuração gerada. Pareamentos e mensagens reais exigem um aparelho de destino autorizado. Dados operacionais ficam em `WHATSAPP_ENGINEER_HOME`, fora do repositório. Preserve a licença e a atribuição da base.
