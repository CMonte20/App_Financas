# Como instalar e publicar o Saldo Certo

## Opção A: agora, sem publicar nada (5 minutos)
1. No celular, abra esta conversa no app do Claude e baixe o arquivo **financas.html**.
2. Abra o app **Arquivos** do Android, vá em Downloads, toque no arquivo e escolha **Chrome**.
3. Entre com usuário **familia** e senha **Familia@2026** e crie a sua senha.
4. Faça um teste antes de lançar tudo: lance uma conta, feche o Chrome, abra o arquivo de novo e veja se ela continua lá. Se sumir, use a opção B, que é mais confiável.

## Opção B: GitHub Pages, instala como app (15 minutos, grátis)
O GitHub guarda **só o código** do app. Os dados de cada pessoa ficam no celular dela.

1. Crie uma conta em github.com (pode ser pelo navegador do celular).
2. Toque em **+ → New repository**. Nome: `financas`. Deixe **Public** (o GitHub Pages grátis exige público; o código não tem nenhum dado seu). Crie.
3. No repositório, toque em **Add file → Upload files** e envie todos os arquivos desta pasta: `index.html`, `manifest.webmanifest`, `sw.js`, `icon-192.png`, `icon-512.png`, `icon-maskable-512.png`, `.nojekyll`, `.gitignore`, `README.md`, `PRIVACIDADE.md`. Toque em **Commit changes**.
4. Vá em **Settings → Pages**. Em "Branch", escolha `main` e a pasta `/ (root)`. Salve. Em 1 a 2 minutos aparece o endereço, algo como `https://seuusuario.github.io/financas/`.
5. Abra esse endereço no Chrome do Android. Toque no menu ⋮ → **Instalar app** (ou **Adicionar à tela inicial**). Pronto: ícone na tela, abre em tela cheia e funciona sem internet.
6. No app, em **Ajustes → Segurança**, toque em **Entrar com a digital**.

Para atualizar o app depois: envie o `index.html` novo pelo mesmo caminho (Add file → Upload files). Os dados no celular continuam. Nunca envie backups, faturas ou planilhas para o repositório.

## Opção C: publicar na Google Play
O caminho mais simples, sem programar, é empacotar o site da opção B como app Android (Trusted Web Activity):

1. Faça a opção B primeiro. Para a Play Store, o app precisa estar na raiz de um domínio: use um repositório chamado `seuusuario.github.io` ou um domínio próprio (cerca de R$ 40 por ano no Registro.br).
2. Acesse **pwabuilder.com**, cole o endereço do app e gere o **pacote Android**. Ele entrega um arquivo `.aab` e um `assetlinks.json`.
3. Coloque o `assetlinks.json` no site em `.well-known/assetlinks.json`. É isso que prova ao Android que o app e o site são seus.
4. Crie uma conta de desenvolvedor no **Google Play Console** (taxa única de US$ 25, com verificação de identidade).
5. Crie o app, envie o `.aab` e preencha a ficha:
   - **Segurança dos dados:** "não coleta nem compartilha dados", porque tudo fica no aparelho;
   - **Política de privacidade:** pode ser o link do `PRIVACIDADE.md`;
   - classificação de conteúdo e público-alvo.
6. Contas pessoais novas precisam fazer um **teste fechado com pelo menos 12 testadores por 14 dias** antes de liberar para todos.

Com a Play Store, quem instala não precisa fazer nada além de baixar: o app abre com o ícone, sem pasta nem arquivo para mover.

## O que o GitHub Pages traz e o que fica público
**Ganhos:** hospedagem gratuita; endereço https, que libera instalar como app, entrar com a digital e o backup automático no Google Drive; atualização para todos só trocando o arquivo; histórico de versões.

**O que fica público:** só o código do app. Qualquer pessoa pode abrir o endereço e usar o app (com os dados dela, no celular dela) e pode ver ou copiar o código. **Nenhum dado seu fica lá.**

**Para proteger a autoria:** o arquivo `LICENSE.md` diz que o app é seu, gratuito e sem uso comercial. Se não quiser o código à vista, use o Cloudflare Pages ou o Netlify, que publicam a partir de um repositório **privado** sem custo. O GitHub Pages com repositório privado exige o plano pago.

## Para deixar profissional
- **Domínio próprio** (ex.: financasdafamilia.com.br) no lugar de github.io.
- **Testes em celulares reais:** um Android simples e um mais novo, com faturas de verdade de cada banco (Nubank, Inter, Santander, Caixa, XP), para ajustar a leitura.
- **Versões e novidades:** numerar as versões (1.0, 1.1…) e mostrar "o que mudou" no app.
- **Revisão de segurança** por outra pessoa antes de divulgar para outras famílias.
- **Termos de uso e política de privacidade** revisados (LGPD), mesmo sem coletar dados.
- **Canal de suporte:** um e-mail ou formulário para dúvidas.
- **Sem rastreadores:** manter o app sem analytics nem anúncios, que é o que garante a privacidade.
