export function startBoardFeed({
  read,
  onData = () => {},
  isVisible,
  onVisibility = () => () => {},
  now = Date.now,
  setTimer = setTimeout,
  clearTimer = clearTimeout,
}) {
  let stopped = false;
  let timer;
  let inFlight;
  let activeForce = false;
  let queuedForce = false;
  let latest;
  const schedule = () => {
    clearTimer(timer);
    if (stopped || !isVisible()) return;
    const readAt = Date.parse(latest?.read_at);
    const retryAt = Date.parse(latest?.read_failed?.retry_at);
    const due = latest?.read_failed || !Number.isFinite(readAt) ? now() + 60000 : readAt + 60000;
    timer = setTimer(() => void run(false), Math.max(1000, due - now(), (retryAt || 0) - now()));
  };
  const run = force => {
    if (stopped) return Promise.resolve(latest);
    if (inFlight) {
      if (force && !activeForce) queuedForce = true;
      return inFlight;
    }
    if (!force && !isVisible() && latest) return Promise.resolve(latest);
    clearTimer(timer);
    activeForce = force;
    inFlight = (async () => {
      try {
        do {
          queuedForce = false;
          latest = await read(activeForce);
          if (!stopped) onData(latest);
          activeForce = queuedForce;
        } while (queuedForce && !stopped);
        return latest;
      } finally {
        inFlight = null;
        schedule();
      }
    })();
    return inFlight;
  };
  const unsubscribe = onVisibility(() => {
    clearTimer(timer);
    if (isVisible()) void run(false);
  });
  void run(false);
  return {
    refresh: () => run(true),
    stop() {
      stopped = true;
      clearTimer(timer);
      unsubscribe();
    },
  };
}
