# Site Versal Agro

Cópia estática de [versalagro.com.br](https://versalagro.com.br/) para publicar em `/site`.

As páginas são `index.html`, `sobre.html` e `servicos-versal.html`. CSS e JavaScript do mesmo domínio ficam em `_astro-1790949682290/`. Imagens, fontes, mapa e vídeo continuam nos endereços originais (Zyrosite, Pexels e Google).

Links internos apontam para `/site`, `/site/sobre` e `/site/servicos-versal`.

## Publicação

O Nginx entrega esta pasta em `/site` e encaminha o restante para a agenda em `127.0.0.1:5173`. A configuração está em `deploy/nginx.conf` e entra em `/etc/nginx/conf.d/`, com o site padrão da porta 80 desativado. No servidor, os arquivos ficam em `/var/www/site`.

`http://104.161.32.246` redireciona para `https://104.161.32.246`. O certificado da Let's Encrypt vale para esse IP, dura cerca de seis dias e é renovado pelo timer `deploy/certbot-renew.timer`, que chama o Certbot instalado em `/opt/certbot`. A porta 80 permanece aberta para o desafio de renovação e para o redirecionamento. A porta 443 está liberada no firewall.

O botão **Enviar informações** envia o formulário para `/site/api/contato`. O serviço `deploy/contato.py`, instalado em `/opt/versal-site/contato.py` e iniciado por `deploy/versal-contato.service`, entrega a mensagem em `comercial@versalagro.com.br`, com cópia para `ti@versalagro.com.br`, pelo Postfix local.
