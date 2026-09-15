from tools.ppt_tool import ppt_tool

async def create_ppt(**kwargs):
    return await ppt_tool.arun(**kwargs)

ppt_mcp_tools = {
    "document.create_ppt": create_ppt,
}
