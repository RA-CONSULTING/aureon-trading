const { RuntimeManager } = require('./runtime-manager.cjs');

(async () => {
  const manager = new RuntimeManager();
  const status = await manager.getStatus();
  console.log(JSON.stringify(status, null, 2));
  process.exit(0);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
