// Run one scene's LOGIC in Node. Args: <fxPath> <fxName> <propsJson>; LOGIC on stdin.
// Prints {state, vals}. mk.py reads STATE_SEED and readFx from this file.
const fs = require("fs");
const [fxPath, fxName, propsJson] = process.argv.slice(2);
const logic = fs.readFileSync(0, "utf8");
const props = JSON.parse(propsJson);

const STATE_SEED = { fx: false, toast: "" };
function readFx(win, name) {
  return win[name] || {};
}

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
function setTimeout() {}
function clearTimeout() {}
globalThis.window = window;
globalThis.document = document;
globalThis.setTimeout = setTimeout;
globalThis.clearTimeout = clearTimeout;

const fxSource = fs.readFileSync(fxPath, "utf8");
(0, eval)(fxSource);

class DCLogic {
  constructor(props) {
    this.props = props;
    this.state = Object.assign({}, STATE_SEED, this.init(props));
  }
  setState(partial, cb) {
    this.state = Object.assign({}, this.state, partial);
    if (typeof cb === "function") cb();
  }
  fx() { return readFx(window, fxName); }
  emit() {}
  toast() {}
  init() { return {}; }
  onReady() {}
  afterUpdate() {}
  cleanup() {}
  renderVals() { return {}; }
}

const Component = new Function(
  "DCLogic",
  `return class Component extends DCLogic {\n${logic}\n}`,
)(DCLogic);
const inst = new Component(props);
inst.setState({ fx: true }, () => inst.onReady());
const vals = inst.renderVals();
process.stdout.write(JSON.stringify({
  state: JSON.parse(JSON.stringify(inst.state)),
  vals: JSON.parse(JSON.stringify(vals)),
}));
