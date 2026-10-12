import { NextResponse } from "next/server";
import { jobErrorMessage } from "../../../lib/job-error.ts";
import { RequestError } from "../../../lib/requests.ts";

export async function respond(work: () => Promise<unknown>) {
  try {
    return NextResponse.json(await work());
  } catch (error) {
    if (error instanceof RequestError) return NextResponse.json({ error: error.message }, { status: 400 });
    const message = jobErrorMessage(error);
    return NextResponse.json({ error: message }, { status: /COMFY_API_KEY/.test(message) ? 503 : 502 });
  }
}
