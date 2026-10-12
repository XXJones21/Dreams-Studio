import { getOutput, getOutputLink } from "../../../../../../lib/comfy.ts";
import { jobErrorMessage } from "../../../../../../lib/job-error.ts";
import { parseJobId, RequestError } from "../../../../../../lib/requests.ts";

export const runtime = "nodejs";

export async function GET(_: Request, { params }: { params: Promise<{ id: string; outputId: string }> }) {
  try {
    const { id, outputId } = await params;
    const [jobId, out] = [parseJobId(id), parseJobId(outputId)];
    // A fresh signed URL on every request: Comfy Cloud's links expire after about an hour, the output after 24 hours.
    const link = await getOutputLink(jobId, out);
    if (link) return new Response(null, { status: 302, headers: { Location: link, "Cache-Control": "no-store" } });
    const { bytes, type, name } = await getOutput(jobId, out);
    return new Response(new Blob([bytes as Uint8Array<ArrayBuffer>]), {
      headers: { "Content-Type": type, "Content-Disposition": `inline; filename="${name.replace(/"/g, "")}"`, "Cache-Control": "private, max-age=300" },
    });
  } catch (error) {
    if (error instanceof RequestError) return Response.json({ error: error.message }, { status: 400 });
    return Response.json({ error: jobErrorMessage(error) }, { status: 502 });
  }
}
