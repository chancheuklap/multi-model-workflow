// The floating variant switcher every prototype of this effort shares. Not part of any design.
export function mountSwitcher({keys, names, current, onSwitch}) {
  document.querySelector("[data-prototype-switcher]")?.remove();
  const bar = document.createElement("div");
  bar.dataset.prototypeSwitcher = "";
  bar.setAttribute("role", "toolbar");
  bar.setAttribute("aria-label", "原型方案切换");
  Object.assign(bar.style, {
    position: "fixed", left: "50%", bottom: "16px", transform: "translateX(-50%)", zIndex: "9999",
    display: "flex", alignItems: "center", gap: "10px", padding: "6px 10px", borderRadius: "999px",
    background: "#111", color: "#fff", font: "13px system-ui, sans-serif", boxShadow: "0 4px 16px rgba(0,0,0,.35)",
  });
  const step = delta => onSwitch(keys[(keys.indexOf(current) + delta + keys.length) % keys.length]);
  const arrow = (text, delta, label) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = text;
    b.setAttribute("aria-label", label);
    Object.assign(b.style, {background: "transparent", color: "#fff", border: "0", cursor: "pointer", fontSize: "16px"});
    b.onclick = () => step(delta);
    return b;
  };
  const label = document.createElement("span");
  label.textContent = `原型 ${current}${names[current] ? `（${names[current]}）` : ""}`;
  bar.append(arrow("←", -1, "上一个方案"), label, arrow("→", 1, "下一个方案"));
  document.body.append(bar);
  if (!window._prototypeKeys) {
    window._prototypeKeys = true;
    document.addEventListener("keydown", event => {
      const t = event.target;
      if (t.closest?.("input, textarea, select, [contenteditable]")) return;
      if (event.key === "ArrowLeft") window._prototypeStep?.(-1);
      if (event.key === "ArrowRight") window._prototypeStep?.(1);
    });
  }
  window._prototypeStep = step;
}
