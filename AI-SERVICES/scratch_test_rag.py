import asyncio
from tools.rag_tool import search_knowledge_base

async def main():
    print("Test 1: user_id=None, is_admin=False")
    res1 = search_knowledge_base.invoke({"query": "proposed solution"})
    print("Res1:", len(res1))

    print("Test 2: user_id='6aa4175dfd9dcb2518c85dcc' (uploader), is_admin=False")
    res2 = search_knowledge_base.invoke({"query": "proposed solution", "user_id": "6aa4175dfd9dcb2518c85dcc", "is_admin": False})
    print("Res2:", len(res2))

    print("Test 3: user_id='6a9d4ab9f9754d0fd3f1250e' (other user), is_admin=False")
    res3 = search_knowledge_base.invoke({"query": "proposed solution", "user_id": "6a9d4ab9f9754d0fd3f1250e", "is_admin": False})
    print("Res3:", res3)

if __name__ == "__main__":
    asyncio.run(main())
