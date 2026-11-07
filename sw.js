// Guarda os arquivos do app no celular: ele abre e funciona sem internet. Nenhum dado pessoal passa por aqui.
// Versão nova só entra quando a pessoa toca em "Atualizar".
const CACHE='financas-b671788617';
const FILES=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES.map(f=>new Request(f,{cache:'reload'})))))});
self.addEventListener('message',e=>{ if(e.data==='atualizar') self.skipWaiting(); });
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE&&k!=='compartilhado').map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  // Compartilhar → Saldo Certo (Android): guarda a fatura só até o app abrir e ler; depois é apagada
  if(e.request.method==='POST'&&u.origin===location.origin&&u.pathname.endsWith('/compartilhar')){ e.respondWith((async()=>{ try{ const fd=await e.request.formData(); const f=fd.get('fatura'); if(f&&f.size){ const c=await caches.open('compartilhado'); await c.put('./fatura-compartilhada',new Response(f,{headers:{'content-type':f.type||'application/pdf','x-nome':encodeURIComponent(f.name||'fatura.pdf')}})); } }catch(err){} return Response.redirect('./#importar',303); })()); return; }
  if(e.request.method!=='GET'||u.origin!==location.origin) return; // Google Drive e outros sites passam direto
  if(e.request.mode==='navigate'){ e.respondWith(caches.match('./index.html').then(r=>r||fetch(e.request))); return; }
  e.respondWith(caches.match(e.request,{ignoreSearch:true}).then(r=>r||fetch(e.request)));
});
