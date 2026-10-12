import { getJob } from "../../../../lib/comfy.ts";
import { parseJobId } from "../../../../lib/requests.ts";
import { respond } from "../../dream/respond.ts";

export const runtime = "nodejs";

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  return respond(async () => getJob(parseJobId((await params).id)));
}
