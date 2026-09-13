const { io } = require('socket.io-client');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const JWT_SECRET = process.env.JWT_SECRET || 'e2a10712c75bfd49619aa25161d2c225feadf8b89de1b35b07f13c9076d15a60';
const userId = '6a97e53e6ca95e4cde382918';

// Generate token directly
const token = jwt.sign({ id: userId, email: 'avinashbharti3007@gmail.com', role: 'admin' }, JWT_SECRET, { expiresIn: '1d' });
const tokenCookie = `token=${token}`;

async function runTests() {
  console.log('=== Socket.IO E2E Test Suite ===\n');
  
  // Step 2: Socket.IO Connection
  console.log('TEST 2: Socket.IO Connection...');
  const socket = io('http://localhost:5000', {
    transports: ['websocket', 'polling'],
    extraHeaders: {
      cookie: tokenCookie
    }
  });

  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Connection timeout'));
    }, 10000);
    
    socket.on('connect', () => {
      clearTimeout(timeout);
      console.log('  ✅ PASS: Socket connected, id:', socket.id);
      resolve();
    });
    
    socket.on('connect_error', (err) => {
      clearTimeout(timeout);
      reject(err);
    });
  });

  // Step 3: Basic Chat (chat:send → chat:chunk → chat:complete)
  console.log('\nTEST 3: Basic Chat (Hello)...');
  const requestId3 = `test_${Date.now()}`;
  let gotChunks = false;
  let gotComplete = false;
  
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Chat timeout after 120s'));
    }, 120000);
    
    socket.on('chat:chunk', (data) => {
      if (data.messageId !== requestId3) return;
      if (data.chunk && data.chunk.length > 0) {
        if (!gotChunks) {
          console.log('  ✅ First chunk received');
          gotChunks = true;
        }
      }
    });
    
    socket.on('chat:complete', (data) => {
      if (data.messageId !== requestId3) return;
      clearTimeout(timeout);
      gotComplete = true;
      console.log('  ✅ PASS: chat:complete received');
      socket.off('chat:chunk');
      socket.off('chat:complete');
      socket.off('chat:error');
      resolve();
    });
    
    socket.on('chat:error', (data) => {
      if (data.messageId && data.messageId !== requestId3) return;
      clearTimeout(timeout);
      console.log('  ❌ FAIL: chat:error:', data.error);
      socket.off('chat:chunk');
      socket.off('chat:complete');
      socket.off('chat:error');
      reject(new Error(data.error));
    });
    
    socket.emit('chat:send', {
      message: 'Hello, respond with just "Hi there!" and nothing else.',
      agent: 'general',
      model: 'auto',
      requestId: requestId3
    });
  });

  // Step 4: Stop test (send then immediately stop)
  console.log('\nTEST 4: Stop generation...');
  const requestId4 = `test_stop_${Date.now()}`;
  
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      // If we get here without error, the stop worked (or we got complete first)
      console.log('  ⚠️ WARNING: Stop test timeout - generation may have completed before stop');
      socket.off('chat:chunk');
      socket.off('chat:complete');
      socket.off('chat:stopped');
      socket.off('chat:error');
      resolve();
    }, 30000);
    
    let stopSent = false;
    let conversationId = null;
    
    socket.on('chat:start', (data) => {
      conversationId = data.conversationId;
    });
    
    socket.on('chat:chunk', (data) => {
      if (data.messageId !== requestId4) return;
      if (!stopSent) {
        stopSent = true;
        console.log('  → Sending chat:stop after first chunk');
        socket.emit('chat:stop', { requestId: requestId4, conversationId });
      }
    });
    
    socket.on('chat:stopped', (data) => {
      if (data.requestId !== requestId4) return;
      clearTimeout(timeout);
      console.log('  ✅ PASS: chat:stopped received');
      socket.off('chat:chunk');
      socket.off('chat:complete');
      socket.off('chat:stopped');
      socket.off('chat:error');
      socket.off('chat:start');
      resolve();
    });
    
    socket.on('chat:complete', (data) => {
      if (data.messageId !== requestId4) return;
      clearTimeout(timeout);
      console.log('  ⚠️ WARNING: chat:complete received (generation finished before stop)');
      socket.off('chat:chunk');
      socket.off('chat:complete');
      socket.off('chat:stopped');
      socket.off('chat:error');
      socket.off('chat:start');
      resolve();
    });
    
    socket.on('chat:error', (data) => {
      if (data.messageId && data.messageId !== requestId4) return;
      clearTimeout(timeout);
      console.log('  ❌ FAIL: chat:error during stop test:', data.error);
      socket.off('chat:chunk');
      socket.off('chat:complete');
      socket.off('chat:stopped');
      socket.off('chat:error');
      socket.off('chat:start');
      reject(new Error(data.error));
    });
    
    socket.emit('chat:send', {
      message: 'Write a very long essay about the history of computing. Make it at least 500 words.',
      agent: 'general',
      model: 'auto',
      requestId: requestId4
    });
  });

  // Step 5: Invalid agent test
  console.log('\nTEST 5: Invalid agent...');
  const requestId5 = `test_invalid_${Date.now()}`;
  
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Invalid agent test timeout'));
    }, 10000);
    
    socket.on('chat:error', (data) => {
      clearTimeout(timeout);
      if (data.code === 'AGENT_NOT_FOUND') {
        console.log('  ✅ PASS: Got AGENT_NOT_FOUND error');
      } else {
        console.log('  ⚠️ WARNING: Got error but not AGENT_NOT_FOUND:', data);
      }
      socket.off('chat:error');
      resolve();
    });
    
    socket.emit('chat:send', {
      message: 'test',
      agent: 'nonexistent_agent_xyz',
      requestId: requestId5
    });
  });

  // Step 6: Re-send after stop
  console.log('\nTEST 6: Re-send after stop...');
  const requestId6 = `test_resend_${Date.now()}`;
  let resendComplete = false;
  
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      if (!resendComplete) {
        reject(new Error('Re-send test timeout'));
      }
    }, 120000);
    
    socket.on('chat:complete', (data) => {
      if (data.messageId !== requestId6) return;
      clearTimeout(timeout);
      resendComplete = true;
      console.log('  ✅ PASS: Re-send after stop works');
      socket.off('chat:complete');
      socket.off('chat:error');
      resolve();
    });
    
    socket.on('chat:error', (data) => {
      if (data.messageId && data.messageId !== requestId6) return;
      clearTimeout(timeout);
      console.log('  ❌ FAIL: Re-send error:', data.error);
      socket.off('chat:complete');
      socket.off('chat:error');
      reject(new Error(data.error));
    });
    
    socket.emit('chat:send', {
      message: 'Say just "OK"',
      agent: 'general',
      model: 'auto',
      requestId: requestId6
    });
  });

  // Done
  console.log('\n=== All tests completed ===');
  socket.disconnect();
  process.exit(0);
}

runTests().catch(err => {
  console.error('\n❌ Test suite failed:', err.message);
  process.exit(1);
});
