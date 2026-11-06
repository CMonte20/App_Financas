# Monta e confere a versão do site do Saldo Certo. Só usa Python, sem instalar nada.
#
#   python3 dev_montar.py conferir            confere a embalagem do index.html do site
#   python3 dev_montar.py versao              põe no sw.js uma versão nova (hash do index.html)
#   python3 dev_montar.py site ARTEFATO.html  traz o código do app do artefato do Claude para o index.html do site
#   python3 dev_montar.py artefato ARTEFATO.html   leva o código do app do site para o artefato (para publicar no Claude)
#
# O index.html do site tem 4 scripts: [0] anti-moldura, [1] __SITE + leitor de PDF embutido (base64),
# [2] PARSER, [3] app. O artefato do Claude tem só [PARSER, app] e carrega o PDF de arquivos ao lado.
# O código do app (PARSER + app) é o mesmo nos dois; só a embalagem muda. NUNCA suba o HTML do artefato no site.
import re, sys, hashlib, os

AQUI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(AQUI, 'index.html')
SW = os.path.join(AQUI, 'sw.js')
RX = r'(<script[^>]*>)(.*?)(</script>)'

def ler(p): return open(p, encoding='utf8').read()
def gravar(p, s): open(p, 'w', encoding='utf8').write(s)

def partes(html):
    """Devolve (lista de matches de <script>, índice do PARSER, índice do app)."""
    ms = list(re.finditer(RX, html, re.S))
    ip = [i for i, m in enumerate(ms) if m.group(2).lstrip().startswith('/* ===================== PARSER')]
    ia = [i for i, m in enumerate(ms) if '===================== utilidades' in m.group(2)[:300]]
    if len(ip) != 1 or len(ia) != 1 or ia[0] != ip[0] + 1:
        sys.exit('Não reconheci os scripts do app (PARSER e utilidades) neste arquivo.')
    return ms, ip[0], ia[0]

def trocar_app(destino, origem):
    md, pd, ad = partes(destino); mo, po, ao = partes(origem)
    return (destino[:md[pd].start(2)] + mo[po].group(2) + destino[md[pd].end(2):md[ad].start(2)]
            + mo[ao].group(2) + destino[md[ad].end(2):])

def conferir(html):
    erros = []
    if 'window.__SITE=true' not in html: erros.append('falta window.__SITE=true')
    if 'window.__PDFJS_B64="' not in html: erros.append('falta o leitor de PDF embutido (__PDFJS_B64)')
    if 'Content-Security-Policy' not in html: erros.append('falta a política de segurança (CSP)')
    if 'manifest.webmanifest' not in html: erros.append('falta o link do manifest (instalar como app)')
    if 'fonts.googleapis.com' in html: erros.append('tem Google Fonts: o CSP do site bloqueia')
    ms, p, a = partes(html)
    return erros

def versao():
    h = hashlib.sha256(open(SITE, 'rb').read()).hexdigest()[:10]
    s = ler(SW); n = re.sub(r"const CACHE='financas-[0-9a-f]*';", f"const CACHE='financas-{h}';", s)
    if n == s and f"financas-{h}" not in s: sys.exit('Não achei a linha const CACHE no sw.js')
    gravar(SW, n); print('sw.js com versão financas-' + h)

cmd = sys.argv[1] if len(sys.argv) > 1 else 'conferir'
if cmd == 'conferir':
    e = conferir(ler(SITE)); print('Embalagem do site OK' if not e else 'PROBLEMAS: ' + '; '.join(e)); sys.exit(1 if e else 0)
elif cmd == 'versao':
    versao()
elif cmd == 'site':
    novo = trocar_app(ler(SITE), ler(sys.argv[2])); e = conferir(novo)
    if e: sys.exit('PROBLEMAS: ' + '; '.join(e))
    gravar(SITE, novo); print('index.html do site atualizado com o código do artefato'); versao()
elif cmd == 'artefato':
    gravar(sys.argv[2], trocar_app(ler(sys.argv[2]), ler(SITE))); print('artefato atualizado com o código do site:', sys.argv[2])
else:
    sys.exit(__doc__ or 'comando desconhecido')
