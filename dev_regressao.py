# Testes de regressão do Saldo Certo (versão do site). Rode SEMPRE antes de entregar uma versão.
#   python3 dev_regressao.py                    testa os arquivos desta pasta e compara com o último commit (HEAD)
#   python3 dev_regressao.py --anterior a87dd5a compara com outro commit (o último que estava bom no ar)
#   python3 dev_regressao.py --sem-comparar     só testa esta pasta
# Precisa: Python 3, pip playwright e o Google Chrome (/usr/bin/google-chrome) ou o Chromium do Playwright.
# Serve os arquivos como http://localhost/App_Financas/ e usa um Chrome de verdade, com service worker e CSP.
import sys, os, json, shutil, subprocess, tempfile, time, socket, argparse
from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
ARQS = ['index.html', 'sw.js', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png']
ap = argparse.ArgumentParser(); ap.add_argument('--anterior', default='HEAD'); ap.add_argument('--sem-comparar', action='store_true')
ARGS = ap.parse_args()

def pasta_de(ref=None):
    d = tempfile.mkdtemp()
    for f in ARQS:
        if ref is None: shutil.copy(os.path.join(AQUI, f), d)
        else: open(os.path.join(d, f), 'wb').write(subprocess.check_output(['git', '-C', AQUI, 'show', f'{ref}:{f}']))
    return d

NOVO = pasta_de()
ANTIGO = None if ARGS.sem_comparar else pasta_de(ARGS.anterior)
M = '2026-11'
RES = []

def ok(nome, cond, det=''):
    RES.append((bool(cond), nome, det))
    print(('  OK  ' if cond else '  FALHOU ') + nome + (f'  [{det}]' if det and not cond else ''))

def porta():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def servir(pasta):
    raiz = tempfile.mkdtemp(); shutil.copytree(pasta, os.path.join(raiz, 'App_Financas'))
    p = porta()
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(p), '--bind', '127.0.0.1', '-d', raiz],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    return srv, f'http://localhost:{p}/App_Financas/'

# dados de exemplo: salário, conta fixa, compras minhas, do Beto, linha antiga de adiantamento (sem dono)
SEED = """(extra)=>{
  S.cfg=normCfg(DEFAULT_CFG); S.cfg.cartoes=[{id:'k1',nome:'Nubank',venc:5},{id:'k2',nome:'Inter',venc:20}]; S.cfg.pessoas=['Beto','Ana'];
  S.lanc=[{id:'l1',tipo:'entrada',desc:'Salário',valor:10000,recorrente:true,mes:'2026-01',ajustes:{}},
          {id:'l2',tipo:'despesa',desc:'Aluguel',valor:2000,recorrente:true,mes:'2026-01',grupo:'Fixo',ajustes:{}}];
  S.compras=[
   {id:'c1',cartao:'k1',desc:'Mercado',valor:1000,mesRef:'2026-11',parcRef:1,nTotal:1,quem:''},
   {id:'c2',cartao:'k1',desc:'Tênis',valor:600,mesRef:'2026-11',parcRef:1,nTotal:1,quem:'Beto'},
   {id:'c3',cartao:'k2',desc:'Celular',valor:310,mesRef:'2026-10',parcRef:1,nTotal:4,quem:'Ana'},
   {id:'c4',cartao:'k2',desc:'Pago antes do fechamento da fatura',valor:-150,mesRef:'2026-11',parcRef:1,nTotal:1,quem:'',origem:'adiantado',tipo:'pagamento',fixo:'-'}];
  // grava pelo mesmo caminho do app (armazenamento local), para os testes valerem depois de cada salvamento
  local=emptyLocal(); local.config.main=S.cfg; for(const l of S.lanc){ const {id,...o}=l; local.lanc[id]=o; } for(const c of S.compras){ const {id,...o}=c; local.compras[id]=o; }
  fromLocal(); if(typeof hideGate==='function') hideGate(); S.mes='2026-11'; render(); return true; }"""

def abrir(b, url, offline_ok=False):
    ctx = b.new_context(viewport={'width': 400, 'height': 900}, service_workers='allow')
    pg = ctx.new_page()
    erros = []
    pg.on('pageerror', lambda e: erros.append('JS: ' + str(e)))
    pg.on('console', lambda m: erros.append('CONSOLE: ' + m.text) if m.type == 'error' and 'favicon' not in m.text else None)
    pg.goto(url); pg.wait_for_timeout(1500)
    return ctx, pg, erros

def numeros(pg):
    return pg.evaluate("""()=>{ const c=calc('2026-11'), g=gastos('2026-11');
      return {saldo:c.saldo, totDes:c.totDes, ent:c.totEnt+c.totReemb, card:c.totCard,
              porGrupo:Object.fromEntries(Object.entries(g.porGrupo).map(([k,v])=>[k,Math.round(v*100)/100])),
              dez:calc('2026-12').saldo, out:calc('2026-10').saldo}; }""")

def pdf_fatura(b):
    pg = b.new_page()
    linhas = ['Fatura do cartão', 'Vencimento: 05/11/2026', 'Total desta fatura R$ 800,00',
              'Total dos lançamentos atuais R$ 1.000,00', '10/10 MERCADO EXTRA 700,00', '12/10 LOJA TENIS 300,00',
              '15/10 PAGAMENTO RECEBIDO -120,00', '20/10 PAGAMENTO RECEBIDO -80,00']
    pg.set_content('<body style="font:14px Arial">' + ''.join(f'<p>{l}</p>' for l in linhas) + '</body>')
    f = tempfile.mktemp(suffix='.pdf'); open(f, 'wb').write(pg.pdf()); pg.close(); return f

def suite_site(b, url, nome):
    print(f'\n== {nome}: site, segurança e instalação')
    ctx, pg, erros = abrir(b, url)
    ok('abre sem erro de JavaScript', not [e for e in erros if e.startswith('JS')], '; '.join(erros)[:300])
    ok('sem bloqueio da política de segurança (CSP)', not [e for e in erros if 'Content Security Policy' in e or 'Refused' in e], '; '.join(erros)[:300])
    ok('marca de site (__SITE) presente', pg.evaluate('!!window.__SITE'))
    ok('leitor de PDF embutido no arquivo', pg.evaluate('!!window.__PDFJS_B64'))
    ok('tela de entrada aparece', pg.evaluate("!document.getElementById('gate').hidden"))
    sw = pg.evaluate("""async()=>{ const r=await Promise.race([navigator.serviceWorker.ready,new Promise(r=>setTimeout(()=>r(null),6000))]); if(!r) return null; await new Promise(r=>setTimeout(r,800)); return (await caches.keys()); }""")
    ok('service worker instalado e com cache', bool(sw) and any(k.startswith('financas-') for k in sw), str(sw))
    ctx.set_offline(True)
    try:
        pg.reload(); pg.wait_for_timeout(1200)
        ok('abre sem internet', pg.evaluate("!!document.getElementById('gate')&&document.body.innerText.length>50"))
    except Exception as e: ok('abre sem internet', False, str(e)[:120])
    ctx.set_offline(False); ctx.close()

def suite_telas(b, url, nome):
    print(f'\n== {nome}: todas as telas com dados')
    ctx, pg, erros = abrir(b, url)
    pg.evaluate(SEED, None)
    for h, mv in [('mes', 'resumo'), ('mes', 'lanc'), ('ano', None), ('cartoes', None), ('importar', None), ('patrimonio', None), ('ajustes', None)]:
        n0 = len(erros)
        pg.evaluate(f"()=>{{ {'S.mesView='+repr(mv)+';' if mv else ''} location.hash='#{h}'; }}"); pg.wait_for_timeout(350)
        txt = pg.evaluate("document.getElementById('main').innerText.length")
        ok(f'tela {h}{"/"+mv if mv else ""} abre', len(erros) == n0 and txt > 50, '; '.join(erros[n0:])[:200])
    # abrir cada cartão e um lançamento
    for k in ['k1', 'k2']:
        n0 = len(erros); pg.evaluate(f"()=>{{ S.card='{k}'; location.hash='#cartoes'; render(); }}"); pg.wait_for_timeout(200)
        ok(f'cartão {k} abre', len(erros) == n0, '; '.join(erros[n0:])[:200])
    n0 = len(erros); pg.evaluate("()=>{ location.hash='#mes'; S.mesView='lanc'; render(); }"); pg.wait_for_timeout(200)
    btn = pg.query_selector('[data-act=editlanc]')
    if btn: btn.click(); pg.wait_for_timeout(200)
    ok('editar lançamento abre', len(erros) == n0 and bool(btn), '; '.join(erros[n0:])[:200])
    n0 = len(erros); planilha = pg.evaluate("()=>JSON.stringify(sheetForMonth('2026-11'))")
    ok('exportar planilha do mês', len(erros) == n0 and len(planilha) > 20)
    ctx.close()
    return planilha

def suite_calculo(b, url, nome):
    print(f'\n== {nome}: números do mês')
    ctx, pg, erros = abrir(b, url); pg.evaluate(SEED, None)
    n = numeros(pg); ctx.close(); return n

def suite_novidades(b, url, pdf):
    print('\n== Novidades de hoje')
    ctx, pg, erros = abrir(b, url); pg.evaluate(SEED, None)
    n = numeros(pg)
    ok('entradas = só o salário (contas dos outros fora)', abs(n['ent'] - 10000) < .01, n['ent'])
    # minha parte nos cartões: Mercado 1000 (Nubank) + adiantamento antigo -150 (Inter, sem dono, continua meu)
    ok('cartões = só minha parte (1000 − 150)', abs(n['card'] - 850) < .01, n['card'])
    info = pg.evaluate("()=>calc('2026-11').tercInfo")
    ok('Beto deve 600 e Ana 310', abs(info['Beto']['v'] - 600) < .01 and abs(info['Ana']['v'] - 310) < .01, info)
    ok('Nubank (dia 5) já venceu; Inter (dia 20) ainda não', info['Beto']['vencido'] and not info['Ana']['vencido'], info)
    pg.evaluate("()=>{ location.hash='#mes'; S.mesView='resumo'; render(); }"); pg.wait_for_timeout(200)
    ok('quadro "Contas dos outros" aparece', 'Contas dos outros' in pg.inner_text('#main'))
    ok('botões Pagou/Não pagou só para quem já venceu', pg.query_selector('[data-act=terc][data-p=Beto]') and not pg.query_selector('[data-act=terc][data-p=Ana]'))
    ok('aviso para responder se pagou', pg.evaluate("()=>alertas('2026-11').some(a=>a.t.includes('pagaram a parte deles'))"))
    pg.click('[data-act=terc][data-p=Beto][data-v=nao]'); pg.wait_for_timeout(300)
    n2 = numeros(pg)
    ok('"Não pagou" vira gasto meu (+600)', abs(n2['card'] - 1450) < .01 and abs(n2['saldo'] - (n['saldo'] - 600)) < .01, n2)
    ok('"Não pagou" entra no plano', any('Beto não pagou' in i['desc'] for i in pg.evaluate("()=>gastos('2026-11').items")))
    ok('gastos mostram "que outros não pagaram"', 'outros não pagaram' in pg.inner_text('#main'))
    pg.click('[data-act=terc][data-p=Beto][data-v=pago]'); pg.wait_for_timeout(300)
    ok('"Pagou" volta ao normal', abs(numeros(pg)['card'] - 850) < .01)
    ok('chip "pagou ✓"', 'pagou ✓' in pg.inner_text('#main'))
    ok('Patrimônio e Faturas com ícones novos', pg.evaluate("()=>{const a=document.querySelectorAll('#tabs a svg'); return [...a].some(s=>s.innerHTML.includes('circle cx=\"18.5\"'))&&[...a].some(s=>s.innerHTML.includes('M12 18v-7'))}"))

    print('\n== Conferência com PDF de verdade (pelo botão de arquivo)')
    pg.evaluate("()=>{ S.card='k1'; location.hash='#importar'; S.imp=null; render(); }"); pg.wait_for_timeout(200)
    ok('dica "Compartilhar → Saldo Certo" (site)', 'Compartilhar' in pg.inner_text('#main'))
    n0 = len(erros)
    pg.set_input_files('#impFile', pdf); pg.wait_for_timeout(3500)
    st = pg.evaluate("()=>S.imp&&S.imp.stage")
    ok('PDF lido e conferência aberta', st == 'review' and len(erros) == n0, f'{st} {erros[n0:]}')
    if st != 'review':
        ctx.close(); return
    I = pg.evaluate("()=>({rows:S.imp.rows.length,total:S.imp.total,compras:S.imp.compras,mes:S.imp.mes,adi:S.imp.adiList,ok:S.imp.cardOk})")
    ok('leu 4 linhas, total 800, compras 1000, mês 2026-11', I['rows'] == 4 and I['total'] == 800 and I['compras'] == 1000 and I['mes'] == M, I)
    ok('2 adiantamentos separados (120 e 80)', [a['v'] for a in I['adi']] == [120, 80], I['adi'])
    ok('aplicar bloqueado até confirmar o cartão', pg.is_disabled('[data-act=impdo]'))
    pg.click('[data-act=impcardsel][data-id=k2]'); pg.wait_for_timeout(250)
    ok('cartão confirmado libera aplicar', not pg.is_disabled('[data-act=impdo]'))
    pg.click('[data-act=adiq][data-i="1"][data-v=outro]'); pg.wait_for_timeout(150)
    pg.select_option('[data-adip="1"]', 'Beto'); pg.wait_for_timeout(150)
    pg.select_option('[data-adimes="0"]', '2026-11'); pg.wait_for_timeout(150)
    pg.click('[data-act=impdo]'); pg.wait_for_timeout(1200)
    r = pg.evaluate("()=>({stage:S.imp&&S.imp.stage, ad:S.compras.filter(c=>c.origem==='adiantado'&&c.cartao==='k2'&&c.mesRef==='2026-11').map(c=>[c.valor,c.quem]), lanc:S.lanc.filter(l=>l.origem==='adiantado').map(l=>[l.valor,l.mes])})")
    ok('conferência aplicada', r['stage'] == 'done', r)
    ok('adiantamento 120 meu e 80 do Beto', sorted(r['ad']) == sorted([[-120, ''], [-80, 'Beto']]), r['ad'])
    ok('saída de 120 no mês escolhido (nov)', r['lanc'] == [[120, '2026-11']], r['lanc'])
    sandro = pg.evaluate("()=>calc('2026-11').tercInfo.Beto.v")
    ok('Beto passa a dever 600 − 80 = 520', abs(sandro - 520) < .01, sandro)
    k2 = pg.evaluate("()=>{const k=calc('2026-11').cards.find(k=>k.id==='k2'); return {conta:k.conta,itens:k.itens.map(x=>[x.desc,x.valor,x.quem])}}")
    # Inter: minhas compras 700+300, menos o meu adiantamento de 120; a parcela da Ana (310) e o adiantamento do Beto (−80) ficam com eles
    ok('cartão Inter = só minha parte (1000 − 120)', abs(k2['conta'] - 880) < .01, k2)

    print('\n== Segunda fatura no mesmo cartão')
    pg.evaluate("()=>{ S.imp=null; location.hash='#importar'; render(); }"); pg.wait_for_timeout(200)
    pg.set_input_files('#impFile', pdf); pg.wait_for_timeout(3000)
    ok('cartão não vem confirmado sozinho', pg.evaluate("()=>S.imp&&S.imp.stage==='review'&&!S.imp.cardOk"))
    pg.click('[data-act=impcardsel][data-id=k2]'); pg.wait_for_timeout(250)
    t = pg.inner_text('#main')
    ok('aviso de fatura já conferida', 'já tem a fatura de' in t and 'Aplicar mesmo assim' in t)
    pg.click('[data-act=impreset]'); pg.wait_for_timeout(200)

    print('\n== Desfazer conferência')
    pg.evaluate("()=>{ S.card='k2'; location.hash='#cartoes'; render(); }"); pg.wait_for_timeout(200)
    pg.click('[data-act=undoask]'); pg.wait_for_timeout(200); pg.click('[data-act=undodo]'); pg.wait_for_timeout(800)
    r = pg.evaluate("()=>({ad:S.compras.filter(c=>c.origem==='adiantado'&&c.cartao==='k2'&&c.mesRef==='2026-11').length, lanc:S.lanc.filter(l=>l.origem==='adiantado').length, conf:!!S.conf['k2_2026-11']})")
    ok('desfazer remove adiantamentos e saída (volta à linha antiga)', r['ad'] == 1 and r['lanc'] == 0 and not r['conf'], r)
    ok('sem erros durante a conferência', not erros, '; '.join(erros)[:300])
    ctx.close()

def suite_atualizacao(b, antigo, novo):
    """Publica a versão anterior, instala, depois publica a nova por cima: o app tem de avisar e trocar de versão."""
    print('\n== Atualização no celular (anterior instalada → nova publicada por cima)')
    if '__SITE=true' not in open(os.path.join(antigo, 'index.html'), encoding='utf8').read():
        print('  (pulado: a versão anterior não é versão de site, então não procura atualização. Use --anterior com um commit bom.)'); return
    raiz = tempfile.mkdtemp(); pasta = os.path.join(raiz, 'App_Financas'); shutil.copytree(antigo, pasta)
    p = porta(); srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(p), '--bind', '127.0.0.1', '-d', raiz], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
    try:
        ctx = b.new_context(); pg = ctx.new_page(); url = f'http://localhost:{p}/App_Financas/'
        pg.goto(url); pg.wait_for_timeout(2500)
        for f in ARQS: shutil.copy(os.path.join(novo, f), pasta)
        pg.reload(); pg.wait_for_timeout(3500)
        ok('aviso "Versão nova do app disponível" aparece', pg.query_selector('.updbar') is not None)
        if pg.query_selector('#updNow'):
            pg.click('#updNow'); pg.wait_for_timeout(4500)
        cache = pg.evaluate("async()=>(await caches.keys()).filter(k=>k.startsWith('financas-'))")
        esperado = [l for l in open(os.path.join(novo, 'sw.js'), encoding='utf8').read().split("'") if l.startswith('financas-')][0]
        ok('depois de "Atualizar" roda a versão nova', cache == [esperado] and pg.evaluate('!!window.__SITE'), f'{cache} esperado {esperado}')
        ok('a versão nova também procura atualizações (tem __SITE)', pg.evaluate('!!window.__SITE'))
        ctx.close()
    finally: srv.terminate()

# O que foi retirado DE PROPÓSITO (decisão do dono). Tudo o mais que existia antes tem de continuar existindo.
REMOVIDOS_DE_PROPOSITO = {
    'faturas/conferência': {'campo #impCard', 'campo #impAdiant'},  # trocados pelos botões de cartão e pela pergunta "Quem pagou?"
    'mes/lanc': {'texto: paga a própria parte nos cartões'},          # contas dos outros saíram das Entradas e foram para o quadro próprio
}
INVENT = """()=>{ const out=new Set(); document.querySelectorAll('#main details').forEach(d=>d.open=true);
  const raiz=document.querySelector('#main');
  raiz.querySelectorAll('[data-act]').forEach(e=>out.add('ação '+e.dataset.act));
  raiz.querySelectorAll('input[id],select[id],textarea[id]').forEach(e=>out.add('campo #'+e.id));
  raiz.querySelectorAll('input[name],select[name]').forEach(e=>out.add('campo '+e.name));
  raiz.querySelectorAll('h1,h2,h3,summary,.eyebrow').forEach(e=>{ const t=e.textContent.trim().replace(/\\s+/g,' '); if(t&&!/\\d/.test(t)) out.add('título: '+t); });
  raiz.querySelectorAll('button,a.btn,label.btn').forEach(e=>{ const t=e.textContent.trim().replace(/\\s+/g,' '); if(t&&t.length<40&&!/\\d/.test(t)) out.add('botão: '+t); });
  raiz.querySelectorAll('.chip').forEach(e=>{ const t=e.textContent.trim(); if(t&&!/\\d/.test(t)) out.add('texto: '+t); });
  document.querySelectorAll('#tabs a').forEach(a=>out.add('aba '+a.getAttribute('href')));
  return [...out]; }"""
TELAS = [('mes/resumo', "S.mesView='resumo'; location.hash='#mes'"), ('mes/lanc', "S.mesView='lanc'; location.hash='#mes'"),
         ('ano', "location.hash='#ano'"), ('cartoes/k1', "S.card='k1'; location.hash='#cartoes'"), ('cartoes/k2', "S.card='k2'; location.hash='#cartoes'"),
         ('faturas', "S.imp=null; location.hash='#importar'"), ('patrimonio', "location.hash='#patrimonio'"), ('ajustes', "location.hash='#ajustes'"),
         ('faturas/conferência', "S.imp={stage:'review',how:'pdf',card:'k1',cardOk:true,mes:'2026-11',rows:[{data:'10/10',desc:'Mercado',valor:700,tipo:'compra'},{data:'15/10',desc:'Pagamento',valor:-120,tipo:'pagamento'}],total:580,compras:700,text:'x',portMap:{},mesAuto:true}; reconc(); location.hash='#importar'")]

def inventario(b, url):
    ctx, pg, erros = abrir(b, url); pg.evaluate(SEED, None); r = {}
    for nome, js in TELAS:
        pg.evaluate("()=>{ " + js + "; render(); }"); pg.wait_for_timeout(350); r[nome] = set(pg.evaluate(INVENT))
    ctx.close(); return r

def suite_inventario(b, urlA, urlN):
    print('\n== Inventário: nada que existia pode sumir (botões, campos, seções, abas)')
    A, N = inventario(b, urlA), inventario(b, urlN)
    for tela in A:
        sumiu = sorted(A[tela] - N[tela] - REMOVIDOS_DE_PROPOSITO.get(tela, set()))
        ok(f'tela {tela}: {len(A[tela])} itens de antes continuam', not sumiu, 'SUMIU: ' + ' | '.join(sumiu))

with sync_playwright() as p:
    b = p.chromium.launch(**({'executable_path': '/usr/bin/google-chrome'} if os.path.exists('/usr/bin/google-chrome') else {}), args=['--no-sandbox'])
    srvN, urlN = servir(NOVO)
    try:
        suite_site(b, urlN, 'NOVA')
        planN = suite_telas(b, urlN, 'NOVA')
        ok('planilha não põe contas dos outros em Entradas', '(cartões)' not in planN)
        nN = suite_calculo(b, urlN, 'NOVA')
        if ANTIGO:
            srvA, urlA = servir(ANTIGO)
            try:
                nA = suite_calculo(b, urlA, f'ANTERIOR ({ARGS.anterior}), só para comparar')
                suite_inventario(b, urlA, urlN)
            finally: srvA.terminate()
            suite_atualizacao(b, ANTIGO, NOVO)
            print('\n== Comparação com a versão anterior (o que não podia mudar)')
            ok('sobra do mês igual', abs(nA['saldo'] - nN['saldo']) < .01, f"{nA['saldo']} vs {nN['saldo']}")
            ok('sobra de outubro e dezembro iguais', abs(nA['out'] - nN['out']) < .01 and abs(nA['dez'] - nN['dez']) < .01, f"{nA} {nN}")
            ok('contas fixas iguais', abs(nA['totDes'] - nN['totDes']) < .01)
            ok('plano por grupo igual', nA['porGrupo'] == nN['porGrupo'], f"{nA['porGrupo']} vs {nN['porGrupo']}")
            ok('entradas caem exatamente o que era dos outros', abs((nA['ent'] - nN['ent']) - (nA['card'] - nN['card'])) < .01, f"{nA} {nN}")
        suite_novidades(b, urlN, pdf_fatura(b))
    finally:
        srvN.terminate(); b.close()

f = [r for r in RES if not r[0]]
print(f'\nRESULTADO: {len(RES)-len(f)} de {len(RES)} testes passaram')
for r in f: print('  FALHOU:', r[1], r[2])
sys.exit(1 if f else 0)
