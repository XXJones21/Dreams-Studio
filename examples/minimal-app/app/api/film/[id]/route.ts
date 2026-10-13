import { checkFilm } from "../../../../lib/comfy";

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return Response.json(await checkFilm(id));
}
