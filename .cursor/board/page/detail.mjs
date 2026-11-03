import {fromBoard as original, render as renderLayout, find} from './detail-layout.mjs';
import {el, hhmm} from './shared.mjs';
export {find, unmount} from './detail-layout.mjs';

export function fromBoard(payload, selected, now) {
  const view = original(payload, selected, now);
  const found = find(payload.tasks || [], selected);
  if (found?.type !== 'ticket') return view;
  const ticket = found.ref;
  view.noRunText = '云端 Agent 的活动由 Coordinator 通过原生子任务查看。';
  view.blockers = ticket.blockers.map(child => ({
    n: child.number, num: '#' + child.number, title: child.title,
    lamp: child.resolved ? 'ink' : 'orange', hold: !child.resolved,
    state: child.resolved ? 'resolved' : 'unresolved',
  }));
  view.kids = ticket.children.map(child => ({
    num: '#' + child.number, title: child.title, kind: 'child',
    lamp: child.state === 'closed' ? 'ink' : 'hollow', hot: false,
  }));
  view.phaseBlocks = [];
  view.eventCount = ticket.comments.length;
  view.comments = ticket.comments;
  return view;
}

export function render(host, view, api, hooks) {
  const root = renderLayout(host, view, api, hooks);
  const records = host.querySelector('[data-ui="详情.events"]');
  if (records && view.comments) {
    records.replaceChildren(
      el('div', {class: 'section-head'}, el('span', {class: 'eyebrow'}, 'GitHub 工作记录'),
        el('span', {class: 'meta'}, String(view.comments.length))),
      ...view.comments.map(comment => el('article', {class: 'log-block'},
        el('div', {class: 'log-head'},
          el('span', {class: 'log-n'}, comment.user?.login || 'GitHub'),
          el('time', {class: 'log-time', datetime: comment.created_at}, hhmm(comment.created_at))),
        el('div', {class: 'log-body', style: 'white-space:pre-wrap;overflow-wrap:anywhere;padding:12px'}, comment.body || ''))),
    );
  }
  return root;
}
