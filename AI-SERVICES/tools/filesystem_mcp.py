async def list_directory(**kwargs):
    return {"success": True, "output": "list_directory not implemented"}

async def read_file(**kwargs):
    return {"success": True, "output": "read_file not implemented"}

async def create_file(**kwargs):
    return {"success": True, "output": "create_file not implemented"}

async def write_file(**kwargs):
    return {"success": True, "output": "write_file not implemented"}

async def create_directory(**kwargs):
    return {"success": True, "output": "create_directory not implemented"}

async def rename_file(**kwargs):
    return {"success": True, "output": "rename_file not implemented"}

async def move_file(**kwargs):
    return {"success": True, "output": "move_file not implemented"}

async def delete_file(**kwargs):
    return {"success": True, "output": "delete_file not implemented"}

async def file_exists(**kwargs):
    return {"success": True, "output": "file_exists not implemented"}

async def metadata(**kwargs):
    return {"success": True, "output": "metadata not implemented"}

filesystem_mcp_tools = {
    "filesystem.list_directory": list_directory,
    "filesystem.read_file": read_file,
    "filesystem.create_file": create_file,
    "filesystem.write_file": write_file,
    "filesystem.create_directory": create_directory,
    "filesystem.rename_file": rename_file,
    "filesystem.move_file": move_file,
    "filesystem.delete_file": delete_file,
    "filesystem.file_exists": file_exists,
    "filesystem.metadata": metadata
}
