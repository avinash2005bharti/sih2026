const axios = require('axios');

async function testFastAPIStream() {
  console.log('Sending streaming request to FastAPI...');
  const start = Date.now();
  try {
    const res = await axios.post(
      'http://127.0.0.1:8000/api/chat/stream',
      {
        message: 'hello',
        conversation_id: 'test_conv_stream',
        user_id: '6a97e53e6ca95e4cde382918',
        model: 'auto',
        agent: 'auto'
      },
      {
        responseType: 'stream',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        timeout: 60000
      }
    );

    console.log('Stream response status:', res.status);
    console.log('Stream response headers:', res.headers);

    res.data.on('data', (chunk) => {
      console.log(`[CHUNK at +${Date.now() - start}ms]:`, chunk.toString());
    });

    res.data.on('end', () => {
      console.log(`Stream END at +${Date.now() - start}ms`);
      process.exit(0);
    });

    res.data.on('error', (err) => {
      console.error('Stream ERROR:', err);
      process.exit(1);
    });
  } catch (err) {
    console.error('Request failed:', err.response?.data || err.message);
    process.exit(1);
  }
}

testFastAPIStream();
