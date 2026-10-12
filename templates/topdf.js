// Export a fullscreen HTML deck to a print-faithful PDF via Chrome CDP.
// Usage: node topdf.js <input.html> <output.pdf>
// Requires the deck's shell to have @media print rules with
//   @page{size:1600px 900px;margin:0}
//   .slide:last-of-type{break-after:auto;page-break-after:auto}
//   html,body{...background:var(--bg)}   (NOT white, else side bars in fullscreen)
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const inFile = path.resolve(process.argv[2]);
const outFile = path.resolve(process.argv[3]);
const port = 9400 + Math.floor(Math.random() * 500);
const chrome = spawn(CHROME, [
  '--headless', '--disable-gpu',
  '--remote-debugging-port=' + port,
  '--user-data-dir=/tmp/cdppdf-' + port,
  '--window-size=1600,900', '--force-device-scale-factor=1',
  'about:blank'
], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await sleep(1500);
  const targets = await (await fetch('http://127.0.0.1:' + port + '/json')).json();
  const t = targets.find(x => x.type === 'page');
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  let id = 0; const pending = {};
  const send = (m, p = {}) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  await new Promise(r => ws.onopen = r);
  ws.onmessage = e => { const d = JSON.parse(e.data); if (d.id && pending[d.id]) { pending[d.id](d.result); delete pending[d.id]; } };
  await send('Page.enable');
  await send('Page.navigate', { url: 'file://' + inFile + '#1' });
  await sleep(3500); // let fonts + base64 assets settle
  const r = await send('Page.printToPDF', {
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: false,
    marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0
  });
  fs.writeFileSync(outFile, Buffer.from(r.data, 'base64'));
  console.log(JSON.stringify({ out: outFile, bytes: fs.statSync(outFile).size }));
  ws.close(); chrome.kill(); process.exit(0);
})().catch(e => { console.error(e); chrome.kill(); process.exit(1); });
