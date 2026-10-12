// Lists every node in an API-format workflow with its id and literal inputs: the ids your code sets.
import { readFileSync } from "node:fs";

const file = process.argv[2];
if (!file) throw new Error("Usage: npm run inspect -- workflows/dream_film.api.json");
const graph = JSON.parse(readFileSync(file, "utf8")) as Record<string, { class_type: string; inputs: Record<string, unknown> }>;
for (const [id, node] of Object.entries(graph)) {
  const literals = Object.entries(node.inputs).filter(([, v]) => !Array.isArray(v)).map(([k, v]) => `${k}=${JSON.stringify(v)}`);
  console.log(id.padStart(5), node.class_type.padEnd(30), literals.join("  ").slice(0, 160));
}
