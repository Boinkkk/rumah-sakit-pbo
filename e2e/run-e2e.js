const { spawnSync } = require('child_process');

const mode = process.argv[2] || 'demo';
const isDemo = mode === 'demo';

const env = {
  ...process.env,
  SLOW_MO: process.env.SLOW_MO ?? (isDemo ? '450' : '0'),
  PAUSE_SCALE: process.env.PAUSE_SCALE ?? (isDemo ? '1' : '0'),
};

const args = ['playwright', 'test', ...(isDemo ? ['--headed'] : []), ...process.argv.slice(3)];

const res = spawnSync('npx', args, {
  stdio: 'inherit',
  shell: true,
  env,
});

process.exit(res.status ?? 1);
