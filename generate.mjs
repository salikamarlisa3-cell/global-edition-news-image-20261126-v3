// generate.mjs — authoring-side build for the news-image-20261126 entry.
//
//   node generate.mjs
//
// Step 1 runs build_poster.py, which emits poster.svg from the story
// data (the SVG is a build artifact and is never committed). Step 2
// renders that SVG to entry.png at exactly 1024x1024 with a local
// Chromium headless build. No network is touched: the SVG is fully
// self-contained and the browser only ever opens a file:// URL.
//
// The competition program (main.ts) does not use this file; it simply
// delivers the committed entry.png.

import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, renameSync, rmSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = fileURLToPath(new URL('.', import.meta.url));

execFileSync('python3', [join(here, 'build_poster.py')],
             { cwd: here, stdio: 'inherit' });

// Locate a Chromium binary: explicit override first, then the usual
// PATH names, then the Playwright browser cache.
function findChromium() {
  const candidates = [];
  if (process.env.CHROMIUM_BIN) candidates.push(process.env.CHROMIUM_BIN);
  for (const name of ['chromium', 'chromium-browser', 'google-chrome',
                      'google-chrome-stable']) {
    for (const dir of (process.env.PATH ?? '').split(':')) {
      if (dir) candidates.push(join(dir, name));
    }
  }
  const cache = join(homedir(), '.cache', 'ms-playwright');
  if (existsSync(cache)) {
    for (const dir of readdirSync(cache).sort().reverse()) {
      if (dir.startsWith('chromium_headless_shell')) {
        candidates.push(join(cache, dir, 'chrome-headless-shell-linux64',
                             'chrome-headless-shell'));
      } else if (dir.startsWith('chromium')) {
        candidates.push(join(cache, dir, 'chrome-linux', 'chrome'));
      }
    }
  }
  for (const c of candidates) if (existsSync(c)) return c;
  throw new Error('no Chromium binary found (set CHROMIUM_BIN)');
}

const shot = join(here, 'render.png');
rmSync(shot, { force: true });
execFileSync(findChromium(), [
  '--headless',
  '--disable-gpu',
  '--no-sandbox',
  '--hide-scrollbars',
  '--force-device-scale-factor=1',
  '--window-size=1024,1024',
  '--default-background-color=00000000',
  '--screenshot=' + shot,
  pathToFileURL(join(here, 'poster.svg')).href,
], { stdio: 'inherit' });

renameSync(shot, join(here, 'entry.png'));
console.log('entry.png rendered: 1024x1024 from poster.svg');
