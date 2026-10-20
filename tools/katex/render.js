// Render TeX expressions to HTML at build time: stdin JSON [[tex, display], ...] -> stdout JSON [html, ...]
const katex = require("./katex.min.js");
let input = "";
process.stdin.on("data", (d) => (input += d));
process.stdin.on("end", () => {
  const items = JSON.parse(input);
  const out = items.map(([tex, display]) => {
    try {
      return katex.renderToString(tex, { displayMode: display, throwOnError: true, strict: "ignore"});
    } catch (e) {
      return "ERROR:" + e.message;
    }
  });
  process.stdout.write(JSON.stringify(out));
});
