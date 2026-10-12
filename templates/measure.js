// Measure divider/hero layout + detect text wrapping via Chrome CDP.
// Usage: node measure.js <file.html> [page ...]   (default pages: 3 10 19 29)
// IMPORTANT: --window-size=1600,900 --force-device-scale-factor=1 are required,
// otherwise #stage scale != 1 and getBoundingClientRect values are distorted.
// Wrap detection uses round(rect.height / lineHeight). Do NOT use scrollWidth or a
// white-space:nowrap rect — both return the container width, not the text width.
// clientWidth is NOT affected by transform (true layout px).
const { spawn } = require('child_process');
const path = require('path');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const file = 'file://' + path.resolve(process.argv[2]);
const pages = process.argv.slice(3).map(Number);
const target = (pages.length ? pages : [3, 10, 19, 29]);
const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn(CHROME, [
  '--headless', '--disable-gpu',
  '--remote-debugging-port=' + port,
  '--user-data-dir=/tmp/cdpmeas-' + port,
  '--window-size=1600,900', '--force-device-scale-factor=1',
  'about:blank'
], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await sleep(1500);
  const t = (await (await fetch('http://127.0.0.1:' + port + '/json')).json()).find(x => x.type === 'page');
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  let id = 0; const pending = {};
  const send = (m, p = {}) => new Promise(res => { const i = ++id; pending[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  await new Promise(r => ws.onopen = r);
  ws.onmessage = e => { const d = JSON.parse(e.data); if (d.id && pending[d.id]) { pending[d.id](d.result); delete pending[d.id]; } };
  await send('Page.enable');
  for (const pg of target) {
    await send('Page.navigate', { url: file + '#' + pg });
    await sleep(900);
    const expr = `(()=>{
      const hero=document.querySelector('.slide.active .chapter-hero');
      if(!hero)return {pg:${pg},err:'no hero'};
      const mid=hero.children[1];
      const muted=mid.querySelector('.muted');
      const stack=hero.children[2];
      const lh=parseFloat(getComputedStyle(muted).lineHeight);
      const lines=Math.round(muted.getBoundingClientRect().height/lh);
      return {pg:${pg},
        heroW:Math.round(hero.getBoundingClientRect().width),
        numW:Math.round(hero.children[0].getBoundingClientRect().width),
        midW:Math.round(mid.getBoundingClientRect().width),
        stackW:stack?Math.round(stack.getBoundingClientRect().width):null,
        gap:getComputedStyle(hero).columnGap,
        mutedAvail:Math.round(muted.clientWidth),
        mutedLines:lines,
        mutedText:muted.textContent};
    })()`;
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
    console.log(JSON.stringify(r.result.value));
  }
  ws.close(); chrome.kill(); process.exit(0);
})().catch(e => { console.error(e); chrome.kill(); process.exit(1); });
