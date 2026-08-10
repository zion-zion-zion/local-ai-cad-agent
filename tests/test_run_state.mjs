import assert from 'node:assert/strict';
import test from 'node:test';

import {
  createRunState,
  runStateControls,
  transitionRun,
} from '../static/js/run-state.mjs';

test('keeps Stop available when a running Run starts streaming', () => {
  let state = transitionRun(createRunState(), {type: 'run_started'});

  assert.equal(state.phase, 'running');
  assert.deepEqual(runStateControls(state), {
    active: true,
    terminal: false,
    stopVisible: true,
    stopDisabled: false,
    submissionDisabled: true,
    stopping: false,
  });

  state = transitionRun(state, {type: 'stream_started'});
  state = transitionRun(state, {type: 'stream_activity'});

  assert.equal(state.phase, 'streaming');
  assert.equal(runStateControls(state).stopVisible, true);
  assert.equal(runStateControls(state).submissionDisabled, true);
});

test('Stop enters a disabled stopping state until a terminal event arrives', () => {
  let state = transitionRun(createRunState(), {type: 'run_started'});
  state = transitionRun(state, {type: 'stop_requested'});

  assert.equal(state.phase, 'stopping');
  assert.deepEqual(runStateControls(state), {
    active: true,
    terminal: false,
    stopVisible: true,
    stopDisabled: true,
    submissionDisabled: true,
    stopping: true,
  });

  state = transitionRun(state, {type: 'stream_activity'});
  assert.equal(state.phase, 'stopping');

  state = transitionRun(state, {type: 'terminal_stopped'});
  assert.equal(state.phase, 'idle');
  assert.deepEqual(runStateControls(state), {
    active: false,
    terminal: true,
    stopVisible: false,
    stopDisabled: false,
    submissionDisabled: false,
    stopping: false,
  });
});

test('ignores late stream events until a new Run explicitly starts', () => {
  let state = transitionRun(createRunState(), {type: 'run_started'});
  state = transitionRun(state, {type: 'terminal_stopped'});

  state = transitionRun(state, {type: 'stream_activity'});
  assert.equal(state.phase, 'idle');
  assert.equal(runStateControls(state).terminal, true);

  state = transitionRun(state, {type: 'run_started'});
  assert.equal(state.phase, 'running');
  assert.equal(runStateControls(state).terminal, false);
});

test('server activity exposes Stop without reopening a terminal Run', () => {
  let state = transitionRun(createRunState(), {type: 'run_activity'});
  assert.equal(state.phase, 'running');
  assert.equal(runStateControls(state).stopVisible, true);

  state = transitionRun(state, {type: 'terminal_stopped'});
  state = transitionRun(state, {type: 'run_activity'});
  assert.equal(state.phase, 'idle');
  assert.equal(runStateControls(state).terminal, true);
});
