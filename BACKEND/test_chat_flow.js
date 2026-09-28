require('dotenv').config();
const jwt = require('jsonwebtoken');
const axios = require('axios');
const { io } = require('socket.io-client');

async function testFlow() {
  const secret = (process.env.JWT_SECRET || 'default_secret').trim();
  const token = jwt.sign(
    { id: '6a97e53e6ca95e4cde382918', isAdmin: true },
    secret,
    { expiresIn: '7d' }
  );

  console.log('1. Testing REST create chat...');
  const createRes = await axios.post(
    'http://localhost:5000/api/chat',
    { title: 'Test Flow Conversation' },
    { headers: { Cookie: `token=${token}` } }
  );
  console.log('Create chat response:', createRes.data);
  const chatId = createRes.data.chat._id;

  console.log('\n2. Testing REST send message...');
  const sendRes = await axios.post(
    `http://localhost:5000/api/chat/${chatId}/message`,
    { content: 'hello from REST test' },
    { headers: { Cookie: `token=${token}` } }
  );
  console.log('Send message response:', sendRes.data);

  console.log('\n3. Testing Socket.IO chat:send...');
  const socket = io('http://localhost:5000', {
    auth: { token },
    extraHeaders: { Cookie: `token=${token}` },
    withCredentials: true,
    transports: ['websocket', 'polling']
  });

  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Socket timeout')), 30000);

    socket.on('connect', () => {
      console.log('Socket connected:', socket.id);
      socket.emit('chat:send', {
        conversationId: chatId,
        message: 'hello from Socket.IO test',
        model: 'auto',
        agent: 'auto',
        requestId: 'req_test_123'
      });
    });

    socket.on('chat:started', (data) => console.log('chat:started event:', data));
    socket.on('chat:token', (data) => process.stdout.write(data.token));
    socket.on('chat:chunk', (data) => {
      if (data.isComplete) {
        console.log('\nchat:chunk completed!');
      }
    });
    socket.on('chat:complete', (data) => {
      console.log('\nchat:complete event received:', data.response);
      clearTimeout(timeout);
      socket.disconnect();
      resolve();
    });
    socket.on('chat:error', (err) => {
      console.error('\nchat:error event received:', err);
      clearTimeout(timeout);
      socket.disconnect();
      reject(err);
    });
    socket.on('connect_error', (err) => {
      console.error('Socket connect_error:', err.message);
      clearTimeout(timeout);
      socket.disconnect();
      reject(err);
    });
  });

  console.log('\n✅ All chat tests succeeded!');
  process.exit(0);
}

testFlow().catch(err => {
  console.error('\n❌ Test failed:', err.response?.data || err.message);
  process.exit(1);
});
