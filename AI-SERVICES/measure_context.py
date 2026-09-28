import asyncio, time
from memory.context_builder import central_context_builder

async def main():
    s = time.time()
    res = await central_context_builder.build(
        conversation_id='test',
        user_id='6a97e53e6ca95e4cde382918',
        query='Hello Sovereign AI'
    )
    print(f'Context built in {time.time()-s:.2f}s')

if __name__ == '__main__':
    asyncio.run(main())
