async def read(**kwargs):
    return {"success": True, "output": "spreadsheet.read not implemented"}

async def create(**kwargs):
    return {"success": True, "output": "spreadsheet.create not implemented"}

async def update(**kwargs):
    return {"success": True, "output": "spreadsheet.update not implemented"}

async def analyze(**kwargs):
    return {"success": True, "output": "spreadsheet.analyze not implemented"}

async def chart(**kwargs):
    return {"success": True, "output": "spreadsheet.chart not implemented"}

spreadsheet_mcp_tools = {
    "spreadsheet.read": read,
    "spreadsheet.create": create,
    "spreadsheet.update": update,
    "spreadsheet.analyze": analyze,
    "spreadsheet.chart": chart
}
