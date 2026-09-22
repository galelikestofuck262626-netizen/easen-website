// Parse browser scripts without running them or contacting external services.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
let checked = 0;
const failures = [];
function check(code, file, line = 1) {
  checked++;
  try { new vm.Script(code, { filename: file }); }
  catch (error) {
    const offset = Number(error.stack.split('\n')[0].match(/:(\d+)$/)?.[1] || 1);
    failures.push({ file, line: line + offset - 1, error: error.message });
  }
}
function walk(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || ['images', 'videos', 'node_modules', 'tools'].includes(entry.name)) continue;
    const file = path.join(directory, entry.name);
    const relative = path.relative(root, file).replaceAll('\\', '/');
    if (entry.isDirectory()) walk(file);
    else if (file.endsWith('.html')) {
      const text = fs.readFileSync(file, 'utf8');
      for (const match of text.matchAll(/<script\b([^>]*?)>([\s\S]*?)<\/script\s*>/gi)) {
        if (/\bsrc\s*=/.test(match[1]) || /type\s*=\s*["'](?:application\/ld\+json|application\/json|module)/i.test(match[1])) continue;
        const start = match.index + match[0].indexOf('>') + 1;
        check(match[2], relative, text.slice(0, start).split('\n').length);
      }
    } else if (file.endsWith('.js')) check(fs.readFileSync(file, 'utf8'), relative);
  }
}
walk(root);
console.log(JSON.stringify({ checked, failures }, null, 2));
if (failures.length) process.exitCode = 1;
