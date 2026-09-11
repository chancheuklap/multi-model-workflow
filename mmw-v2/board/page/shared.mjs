export function el(tag, attrs = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "disabled") node.disabled = true;
    else if (key === "selected") node.selected = true;
    else if (key === "html") node.innerHTML = value;
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    node.append(typeof kid === "object" ? kid : String(kid));
  }
  return node;
}

export const hhmm = value => new Date(value).toLocaleTimeString("en-GB", {
  hour: "2-digit", minute: "2-digit", hour12: false,
});

export async function hand(method) {
  try {
    return await method();
  } catch {
    return null;
  }
}
