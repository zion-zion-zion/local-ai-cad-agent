const IDLE = 'idle';
const RUNNING = 'running';
const STREAMING = 'streaming';
const STOPPING = 'stopping';

export function createRunState() {
  return {phase: IDLE, terminal: false};
}

export function transitionRun(state, event) {
  if (event.type === 'run_started') {
    return state.phase === STOPPING ? state : {phase: RUNNING, terminal: false};
  }
  if (event.type === 'stream_started' || event.type === 'stream_activity') {
    if (state.terminal || state.phase === STOPPING) return state;
    return {phase: STREAMING, terminal: false};
  }
  if (event.type === 'run_activity') {
    if (state.terminal || state.phase === STOPPING) return state;
    return state.phase === IDLE ? {phase: RUNNING, terminal: false} : state;
  }
  if (event.type === 'stop_requested') {
    return state.phase === IDLE ? state : {phase: STOPPING, terminal: false};
  }
  if (event.type.startsWith('terminal_')) {
    return {phase: IDLE, terminal: true};
  }
  return state;
}

export function runStateControls(state) {
  const active = state.phase !== IDLE;
  const stopping = state.phase === STOPPING;
  return {
    active,
    terminal: state.terminal,
    stopVisible: active,
    stopDisabled: stopping,
    submissionDisabled: active,
    stopping,
  };
}
