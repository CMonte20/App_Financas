# Saldo Certo — guia para continuar o trabalho

Leia isto antes de mexer em qualquer arquivo. Vale para qualquer sessão do Claude ou pessoa que pegar o projeto.

## O que é
App de finanças da família, num único `index.html`, sem servidor. Os dados ficam só no aparelho de cada pessoa (armazenamento local do navegador, protegido por senha). Autor: Cleirton Monte.

Existem **duas cópias do mesmo app**, com o mesmo código e embalagens diferentes:

| | Site (o que a família usa) | Artefato no Claude |
|---|---|---|
| Endereço | https://cmonte20.github.io/App_Financas/ | artefato privado "Finanças da Família" na conta do dono |
| Arquivo | `index.html` deste repositório (~2,7 MB) | `index.html` do artefato (~290 KB) + `pdf.min.mjs` + `pdf.worker.min.mjs` |
| Embalagem | CSP, manifest, ícones, `window.__SITE=true`, leitor de PDF embutido em base64, fontes do sistema | Google Fonts, PDF carregado de arquivos ao lado |

**Regra de ouro: nunca suba o HTML do artefato no site.** Sem a embalagem, o leitor de PDF quebra ("Failed to fetch dynamically imported module …/pdf.min.mjs"), o "Compartilhar → Saldo Certo" some e a atualização automática para. Isso já aconteceu em 06/11/2026.

O `index.html` do site tem 4 scripts: anti-moldura, `__SITE` + PDF embutido, **PARSER** e **app**. Só os dois últimos são o código do app.

## Como fazer uma mudança (sempre nesta ordem)
1. Pegue a versão atual: `git clone https://github.com/cmonte20/app_financas` (repositório público).
2. Edite o código do app direto no `index.html` deste repositório (scripts PARSER e app). Se a mudança foi feita no artefato do Claude, traga com `python3 dev_montar.py site CAMINHO/DO/ARTEFATO.html`.
3. `python3 dev_montar.py conferir`: confere a embalagem do site.
4. `python3 dev_montar.py versao`: atualiza a versão do cache no `sw.js`. **Sem isso, os celulares continuam com a versão antiga.**
5. `python3 dev_regressao.py`: roda os testes de regressão e compara os números com o último commit. **Só entregue com todos passando.** Se o último commit estiver quebrado, compare com o último bom: `--anterior <commit>`.
6. Entregue `index.html` e `sw.js`. Sem acesso de escrita ao GitHub, o dono sobe pelo site do GitHub (Add file → Upload files). Para o Claude fazer o commit, o dono precisa vincular o GitHub em claude.ai → Configurações → Conectores.
7. Atualize o artefato do Claude com o mesmo código: leia o artefato, rode `python3 dev_montar.py artefato ARTEFATO.html` e publique.
8. Anote a mudança no "Histórico" abaixo.

No celular, a versão nova aparece no aviso "Versão nova do app disponível" ou em Ajustes → Procurar atualização. Se o celular estiver preso numa versão sem `__SITE` (sem o botão "Procurar atualização"), recarregar não resolve: feche **todas** as abas do app no Chrome (e o app instalado, nos recentes) e abra de novo. **Nunca peça para limpar os dados do site no Chrome**, porque isso apaga tudo do usuário.

## Testes de regressão (`dev_regressao.py`)
Usa o Chrome de verdade com o site servido em `http://localhost/App_Financas/` e cobre:
- **Site:** abre sem erro, sem bloqueio de CSP, com `__SITE` e PDF embutido, instala o service worker e abre sem internet.
- **Telas:** todas abrem com dados (Mês resumo/lançamentos, Ano, Cartões, Faturas, Patrimônio, Ajustes, editar lançamento, exportar planilha).
- **Comparação com o commit anterior:** sobra de out/nov/dez, contas fixas e plano por grupo devem ficar iguais.
- **Regras de negócio:** contas dos outros, "Pagou/Não pagou", adiantamentos.
- **Fatura em PDF gerada no teste e enviada pelo botão de arquivo:** leitura, confirmação do cartão, aviso de fatura repetida, adiantamentos separados, desfazer.

- **Inventário de funcionalidades:** em cada tela (Mês resumo/lançamentos, Ano, cada cartão, Faturas, conferência, Patrimônio, Ajustes com todas as seções abertas), lista todas as ações, campos, títulos, botões e abas da versão anterior. **Qualquer item que sumir reprova a entrega.** Se algo foi retirado de propósito, com o dono concordando, registre em `REMOVIDOS_DE_PROPOSITO` no `dev_regressao.py`, com o motivo.
- **Atualização no celular:** instala a versão anterior, publica a nova por cima e confere se aparece "Versão nova do app disponível" e se a versão nova continua procurando atualizações.

O objetivo da bateria é **não perder funcionalidade**, não só testar o que mudou. Rodada contra a versão quebrada de 06/11 (HTML do artefato no site), ela reprova 14 itens, incluindo backup, procurar atualização, planilha, modo offline e leitura de PDF.

Ao mudar uma regra, atualize ou acrescente o teste correspondente no mesmo trabalho. Os testes usam nomes fictícios (Ana, Beto). **Este repositório é público: nunca coloque dados reais, faturas ou nomes da família** (o `.gitignore` já bloqueia .pdf, .csv, .json…).

## Regras de negócio decididas com o dono
- **Entradas** são só o que o usuário lança. Nada é somado automaticamente.
- **Contas dos outros:** compra no cartão com "De quem é" preenchido não entra nas Entradas nem nos Gastos do usuário. Fica no quadro "Contas dos outros", com o saldo de cada pessoa (compras − adiantamentos dela).
  - Depois do vencimento da fatura (dia `venc` do cartão), aparecem **Pagou / Não pagou**.
  - Só **"Não pagou"** faz o valor virar gasto do usuário (no cartão e no plano). **Sem resposta = considerado pago.**
  - A resposta fica em `pagos[mês]['tn_'+nome]` (não pagou) e `pagos[mês]['tp_'+nome]` (pagou), com o nome passado por `tercKey()`.
- **Adiantamentos** (pagamento antes do fechamento da fatura) são exceção e tratados **um por um**, como aparecem no PDF. Para cada um, a pergunta é "Quem pagou?":
  - **Eu paguei:** o usuário escolhe o mês em que sai do saldo (data do pagamento, mês anterior ou mês da fatura). Cria uma saída (`lanc`, origem `adiantado`).
  - **Outra pessoa:** não sai do saldo. Com nome, a linha do cartão ganha `quem=nome` e abate o que essa pessoa deve. Sem nome, só abate a fatura.
  - Toda linha fica no cartão como compra negativa (`origem:'adiantado'`, `tipo:'pagamento'`, `fixo:'-'`).
- **Parte do usuário no cartão** = total do cartão − soma de cada pessoa (sem arredondar para zero), + o que outros "não pagaram". Assim a sobra fica igual à das versões antigas.
- **Conferência da fatura:** o cartão precisa ser confirmado tocando nele no topo, e "Aplicar" fica bloqueado até isso. Fatura do mesmo cartão e mês já conferida mostra aviso e o botão "Aplicar mesmo assim". O app sugere o cartão pelas compras conhecidas. Entrando por "Conferir com o PDF" de um cartão, ele já vem confirmado.
- **Ícones:** Patrimônio = casa + moeda. Faturas = documento com seta para cima (envio).

## Backlog
1. **Esconder detalhes técnicos dos erros para o usuário.** Hoje aparecem mensagens como "Failed to fetch dynamically imported module …". Ideia: frase simples do que fazer, e um "Ver detalhes" recolhido com o texto técnico para suporte. **Manter os detalhes visíveis até o fim do período de teste**, por decisão do dono.
2. Limpar os arquivos soltos do repositório (`index (1).html`, `financas (4).html`, `sw (1).js`, e `pdf.min.mjs`/`pdf.worker.min.mjs` se tiverem sido subidos). Não são usados pelo site.
3. Vincular o GitHub ao Claude para os commits saírem direto, com teste antes.
4. Quando alguém adianta mais do que gastou, o saldo da pessoa fica negativo (crédito). Hoje só é exibido. Decidir se abate do mês seguinte.

## Histórico
- **06/11/2026:** contas dos outros fora das Entradas, com "Pagou/Não pagou" depois do vencimento. Adiantamentos um por um, com "Quem pagou?". Confirmação obrigatória do cartão na conferência e aviso de fatura repetida. Novos ícones de Patrimônio e Faturas. Corrigido: a parte do usuário era arredondada para zero e perdia o adiantamento. Corrigido: o HTML do artefato tinha sido subido no site e quebrou a leitura de PDF; o site voltou para a embalagem certa. Criados `dev_montar.py`, `dev_regressao.py` e este guia. Depois, acrescentados à bateria o inventário de funcionalidades e o teste de atualização no celular. Versão no ar (commit 0bc05b5): 64 de 64 testes, comparando com a última boa (a87dd5a).
