// Entry for news-image-20261126 — "The World in One Day", 26 Nov 2026.
//
// The poster beside this file (entry.png, 1024x1024) sums up Thursday
// 26 November 2026: 36 verified stories in 7 regions, 12 of them
// promoted to a front-page leads strip, a "left out & why" date-check
// box, and every story cited in SOURCES.md. The page was designed by
// build_poster.py (which emits poster.svg) and rendered by
// generate.mjs; neither runs here.
//
// This program is delivery only. It copies entry.png, byte for byte,
// into the output directory — $MAKEFUN_OUTPUT_DIR when set, otherwise
// /output as in the grader's container — and then re-reads the copy
// to prove it arrived complete. The judge sees exactly these bytes.

import { copyFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const src = join(dirname(fileURLToPath(import.meta.url)), 'entry.png');
const dst = join(process.env.MAKEFUN_OUTPUT_DIR ?? '/output', 'entry.png');

copyFileSync(src, dst);

const want = statSync(src).size;
const got = statSync(dst).size;
if (got !== want) {
  throw new Error(`delivered entry.png is ${got} bytes, expected ${want}`);
}
console.log(`entry.png delivered to ${dst} (${got} bytes)`);
