"""ComfyUI entry point for the Seamless Continuation nodes."""
from comfy_api.latest import ComfyExtension, io

from .nodes import LastFrame, Stitch


class SeamlessContinuationExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [LastFrame, Stitch]


async def comfy_entrypoint() -> SeamlessContinuationExtension:
    return SeamlessContinuationExtension()
