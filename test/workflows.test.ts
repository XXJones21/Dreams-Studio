import assert from "node:assert/strict";
import test from "node:test";
import { existsSync, readFileSync } from "node:fs";

const graph = JSON.parse(readFileSync("workflows/dream_film.api.json", "utf8")) as Record<string, { class_type: string; inputs: Record<string, unknown> }>;
const roles = JSON.parse(readFileSync("workflows/dream_film.inputs.json", "utf8")) as Record<string, string>;

test("every role points at a real node and input", () => {
  const required = ["style", "keyframe_scene", "avoid", "clip1", "clip2", "clip3", "frames", "generate_keyframe", "keyframe_image",
    "keyframe_seed", "seed1", "seed2", "seed3", "film", "keyframe"];
  for (const role of required) assert.ok(roles[role], `missing role ${role}`);
  for (const [role, path] of Object.entries(roles)) {
    const [node, ...rest] = path.split(".");
    assert.ok(graph[node], `${role}: node ${node} is not in the workflow`);
    if (rest.length) assert.ok(rest.join(".") in graph[node].inputs, `${role}: ${path} has no such input`);
  }
});

test("the outputs are a video save and an image save", () => {
  assert.equal(graph[roles.film].class_type, "SaveVideo");
  assert.equal(graph[roles.keyframe].class_type, "SaveImage");
});

test("API format only, no UI-format keys", () => {
  assert.equal("nodes" in graph, false);
  for (const [id, node] of Object.entries(graph)) {
    assert.equal(typeof node.class_type, "string", `node ${id} has no class_type`);
    assert.equal(typeof node.inputs, "object", `node ${id} has no inputs`);
  }
});

test("the seam crops follow the clip length (Length − 1), so changing the length keeps the seams clean", () => {
  const [lengthNode] = roles.frames.split(".");
  const crops = Object.values(graph).filter((n) => n.class_type === "VideoTemporalCrop");
  assert.equal(crops.length, 2);
  for (const crop of crops) {
    const [mathId] = crop.inputs.length as [string, number];
    const math = graph[mathId];
    assert.equal(math.class_type, "ComfyMathExpression");
    assert.equal(math.inputs.expression, "a - 1");
    assert.deepEqual(math.inputs["values.a"], [lengthNode, 0]);
  }
});

test("Load Image always gets a real file: the default keyframe ships with the app", () => {
  assert.ok(existsSync("workflows/default-keyframe.png"));
});

test("Nano Banana runs only when the switch picks it: no output node reaches it except through the switch", () => {
  const [switchId] = roles.generate_keyframe.split(".");
  const nano = Object.keys(graph).find((id) => graph[id].class_type.startsWith("GeminiNanoBanana"));
  assert.ok(nano);
  // Walk upstream from each output node, stopping at the lazy switch.
  const outputs = Object.keys(graph).filter((id) => ["SaveImage", "SaveVideo", "PreviewImage"].includes(graph[id].class_type));
  for (const out of outputs) {
    const seen = new Set<string>();
    const walk = (id: string) => {
      if (seen.has(id) || id === switchId) return;
      seen.add(id);
      for (const v of Object.values(graph[id].inputs)) if (Array.isArray(v) && typeof v[0] === "string" && graph[v[0]]) walk(v[0]);
    };
    walk(out);
    assert.equal(seen.has(nano!), false, `output node ${out} pulls in Nano Banana regardless of the switch`);
  }
  assert.deepEqual(graph[roles.keyframe].inputs.images, [switchId, 0], "the saved keyframe is whichever one the switch picked");
});

test("the node workflow (dream_film.json) is wired the same as the API export", () => {
  type UiNode = { id: number; type: string; inputs?: { name: string; link: number | null }[] };
  const ui = JSON.parse(readFileSync("workflows/dream_film.json", "utf8")) as { nodes: UiNode[]; links: [number, number, number, number, number, string][] };
  const nodes = new Map(ui.nodes.map((n) => [n.id, n]));
  const links = new Map(ui.links.map((l) => [l[0], l]));
  // Export (API) drops Reroute nodes, so follow them back to the real source.
  const source = (linkId: number): [string, number] => {
    let [, from, slot] = links.get(linkId)!;
    while (nodes.get(from)!.type === "Reroute") [, from, slot] = links.get(nodes.get(from)!.inputs![0].link!)!;
    return [String(from), slot];
  };
  for (const [id, node] of Object.entries(graph)) {
    const uiNode = nodes.get(Number(id));
    assert.ok(uiNode, `node ${id} is missing from the node workflow`);
    assert.equal(uiNode.type, node.class_type, `node ${id} has a different type`);
    for (const [name, v] of Object.entries(node.inputs)) {
      if (!Array.isArray(v)) continue;
      const link: number | null | undefined = uiNode.inputs?.find((i) => i.name === name)?.link;
      assert.ok(typeof link === "number", `node ${id}.${name} is not connected in the node workflow`);
      assert.deepEqual(source(link), v, `node ${id}.${name} is wired differently`);
    }
  }
});
