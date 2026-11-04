import {Board} from './board-layout.mjs';
export {Board};
export {PHASES, defaultExpanded, describeEvent, eventBlocks, blockSummary} from './board-layout.mjs';
export const LAMP_WORD = {orange:'needs attention', green:'PR open', ink:'merged', hollow:'not merged'};
Object.assign(Board, {
  stoppedByFault() { return false; },
  handedBack() { return false; },
  bounce() { return null; },
  running(ticket) { return ticket.prs.some(pr => pr.state === 'open'); },
  done(ticket) { return ticket.landed; },
  cleared(ticket) { return ticket.resolved ?? ticket.landed ?? ticket.blocker_hold === ''; },
  phase(ticket) { return ticket.landed ? 'landed' : this.running(ticket) ? 'verify' : 'queued'; },
  why(ticket) { return ticket.landed ? [] : ticket.reasons.filter(text => text !== 'already merged into the night branch').map(text => ({kind:'record',text})); },
  lamp(ticket) { return ticket.landed ? 'ink' : this.why(ticket).length ? 'orange' : this.running(ticket) ? 'green' : 'hollow'; },
  runLine(ticket) { return {text: ticket.landed ? 'merged into the night branch' : this.running(ticket) ? 'PR awaiting integration' : 'native agent activity is held by Coordinator'}; },
  elapsed() { return ''; },
});
