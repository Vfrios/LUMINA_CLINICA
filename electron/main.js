// Empacota dist/web (copiado para app-web/) numa janela desktop. Não testado neste ambiente (sem rede p/ instalar o Electron).
const { app, BrowserWindow, protocol, net } = require('electron');
const path = require('path'); const { pathToFileURL } = require('url');
// esquema "app://" serve app-web/ como se fosse http (fetch de .glb/.json não funciona via file://)
protocol.registerSchemesAsPrivileged([{ scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true } }]);
app.whenReady().then(() => {
  protocol.handle('app', (req) => {
    const rel = decodeURIComponent(new URL(req.url).pathname) || '/index.html';
    return net.fetch(pathToFileURL(path.join(__dirname, 'app-web', rel === '/' ? 'index.html' : rel)).toString());
  });
  const w = new BrowserWindow({ width: 1280, height: 800, title: 'LÚMINA · Clínica de Estética e Biomedicina', backgroundColor: '#E3D3B5' });
  w.setMenuBarVisibility(false); w.loadURL('app://lumina/index.html');
});
app.on('window-all-closed', () => app.quit());
