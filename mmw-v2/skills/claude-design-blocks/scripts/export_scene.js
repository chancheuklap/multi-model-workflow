// Run one scene through the page's own logic class, the way `support.js` runs it in a
// browser: the whole `<script data-dc-script>` body is evaluated, the class it defines
// is constructed with the scene's props, `componentDidMount` fires, and `renderVals()`
// is read. Args: <propsJson> [fixtureFile...]; the script body on stdin.
// Prints {state, vals}.
const fs = require("fs");
const args = process.argv.slice(2);
const props = JSON.parse(args[0]);
const src = fs.readFileSync(0, "utf8");

// The browser gives the page a window and a document; a logic class registers
// listeners on them and schedules timers. Nothing renders here, so the listeners are
// never called and the timers never fire.
const window = {
  addEventListener() {},
  removeEventListener() {},
  querySelector() { return null; },
};
const document = {
  addEventListener() {},
  removeEventListener() {},
  querySelector() { return null; },
};
globalThis.window = window;
globalThis.document = document;
globalThis.setTimeout = function () {};
globalThis.clearTimeout = function () {};

// Each fixture file assigns its own global (`window.FIXTURES = {...}`), so the runner
// needs no name for it.
for (const file of args.slice(1)) (0, eval)(fs.readFileSync(file, "utf8"));

// `DCLogic` as `support.js` defines it (`StreamableLogic`): props, state, setState,
// the lifecycle hooks and `renderVals`. A page that needs more — `fx()`, `emit()`,
// `toast()`, `init()` — carries it in its own class body, which is why evaluating the
// page's script is enough for a page from any source.
class DCLogic {
  constructor(props) {
    this.props = props || {};
    this.state = {};
  }
  setState(update, cb) {
    const patch = typeof update === "function" ? update(this.state) : update;
    this.state = Object.assign({}, this.state, patch);
    if (typeof cb === "function") cb();
  }
  forceUpdate() {}
  componentDidMount() {}
  componentDidUpdate() {}
  componentWillUnmount() {}
  renderVals() { return {}; }
}

const Component = new Function(
  "DCLogic",
  "StreamableLogic",
  "React",
  src + '\n;return (typeof Component!=="undefined"&&Component)||undefined;',
)(DCLogic, DCLogic, undefined);
if (typeof Component !== "function") {
  throw new Error("the page's script defines no Component class");
}
const inst = new Component(props);
inst.componentDidMount();
const vals = inst.renderVals();
process.stdout.write(JSON.stringify({
  state: JSON.parse(JSON.stringify(inst.state)),
  vals: JSON.parse(JSON.stringify(vals)),
}));
