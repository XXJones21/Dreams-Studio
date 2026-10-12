import { submitFilm } from "../../../../lib/comfy.ts";
import { parseFilm } from "../../../../lib/requests.ts";
import { respond } from "../respond.ts";

export const runtime = "nodejs";

export async function POST(request: Request) {
  return respond(async () => submitFilm(parseFilm(await request.json().catch(() => null))));
}
