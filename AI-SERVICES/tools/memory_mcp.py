async def search(**kwargs):
    return {"success": True, "output": "memory.search not implemented"}

async def add(**kwargs):
    return {"success": True, "output": "memory.add not implemented"}

async def update(**kwargs):
    return {"success": True, "output": "memory.update not implemented"}

async def delete(**kwargs):
    return {"success": True, "output": "memory.delete not implemented"}

async def recent(**kwargs):
    return {"success": True, "output": "memory.recent not implemented"}

memory_mcp_tools = {
    "memory.search": search,
    "memory.add": add,
    "memory.update": update,
    "memory.delete": delete,
    "memory.recent": recent
}
