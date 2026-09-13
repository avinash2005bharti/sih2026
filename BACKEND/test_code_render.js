const { io } = require('socket.io-client');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const token = jwt.sign({ id: '6a97e53e6ca95e4cde382918', email: 'a@a.com', role: 'admin' }, process.env.JWT_SECRET || 'e2a10712c75bfd49619aa25161d2c225feadf8b89de1b35b07f13c9076d15a60', { expiresIn: '1d' });

async function run() {
  const socket = io('http://localhost:5000', { extraHeaders: { cookie: `token=${token}` } });
  socket.on('chat:chunk', data => { if (data.chunk) process.stdout.write(data.chunk); });
  socket.on('chat:complete', data => { console.log('\n\nDONE'); process.exit(0); });
  socket.emit('chat:send', {
    message: 'give me python code for binary search',
    agent: 'coding',
    model: 'auto',
    requestId: 'test_code_render'
  });
}
run();
