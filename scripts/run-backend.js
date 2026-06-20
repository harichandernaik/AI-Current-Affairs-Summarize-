const { existsSync } = require('node:fs');
const { join } = require('node:path');
const { spawn } = require('node:child_process');

const localPython = process.platform === 'win32'
  ? join(process.cwd(), '.venv', 'Scripts', 'python.exe')
  : join(process.cwd(), '.venv', 'bin', 'python');

const python = existsSync(localPython) ? localPython : 'python';
const child = spawn(python, ['backend/app.py'], { stdio: 'inherit', env: process.env });

child.on('exit', code => process.exit(code ?? 0));
