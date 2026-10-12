// Turn a failed job or SDK error into one sentence a person can act on.

export function jobErrorMessage(error: unknown): string {
  const get = (key: string) => (error && typeof error === "object" ? Reflect.get(error, key) : undefined);
  const code = typeof get("code") === "string" ? (get("code") as string) : "";
  const message = typeof error === "string" ? error : typeof get("message") === "string" ? (get("message") as string) : "";
  if (code === "insufficient_credits") return "The workspace is out of Comfy credits. Add credits on platform.comfy.org and try again.";
  if (code === "unauthorized") return "Comfy rejected the API key. Check COMFY_API_KEY in .env.local and restart the app.";
  if (/login first to use this node/i.test(message)) {
    return "A partner node (Nano Banana) rejected the key. Check that COMFY_API_KEY has partner-node access, or use your own keyframe image.";
  }
  const node = message.match(/Node ['"]([^'"]+)['"] not found/i)?.[1];
  if (node) return `This Comfy server has no “${node}” node. Run the app against Comfy Cloud, or install it.`;
  const model = message.match(/['"]([^'"]+\.(?:safetensors|pth|ckpt|gguf))['"] not in/i)?.[1];
  if (model) return `This Comfy server has no model file “${model}”.`;
  return message || "Comfy could not run this job. Try again; if it repeats, check the job in Comfy Cloud.";
}
