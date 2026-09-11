export function startBoardFeed({
  read,
  onData = () => {},
  isVisible,
  setTimer = setInterval,
  clearTimer = clearInterval,
}) {
  let stopped = false;
  const run = async force => {
    if (stopped || (!force && !isVisible())) return;
    onData(await read());
  };
  void run(true);
  const timer = setTimer(() => void run(false), 60000);
  return {
    refresh: () => run(true),
    stop() {
      stopped = true;
      clearTimer(timer);
    },
  };
}
