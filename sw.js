// Guarda os arquivos do app no celular: ele abre e funciona sem internet. Nenhum dado pessoal passa por aqui.
// Versão nova só entra quando a pessoa toca em "Atualizar".
const CACHE='financas-73ebdd1bc7';
const FILES=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES.map(f=>new Request(f,{cache:'reload'})))))});
self.addEventListener('message',e=>{ if(e.data==='atualizar') self.skipWaiting(); });
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(e.request.method!=='GET'||u.origin!==location.origin) return; // Google Drive e outros sites passam direto
  if(e.request.mode==='navigate'){ e.respondWith(caches.match('./index.html').then(r=>r||fetch(e.request))); return; }
  e.respondWith(caches.match(e.request,{ignoreSearch:true}).then(r=>r||fetch(e.request)));
});
