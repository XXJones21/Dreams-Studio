import { makeFilm } from "../../../lib/comfy";

export async function POST(request: Request) {
  const { style } = await request.json();
  return Response.json({ id: await makeFilm(style) });
}
