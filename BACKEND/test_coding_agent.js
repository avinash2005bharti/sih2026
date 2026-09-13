const { io } = require('socket.io-client');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const JWT_SECRET = process.env.JWT_SECRET || 'e2a10712c75bfd49619aa25161d2c225feadf8b89de1b35b07f13c9076d15a60';
const token = jwt.sign({ id: '6a97e53e6ca95e4cde382918', email: 'avinashbharti3007@gmail.com', role: 'admin' }, JWT_SECRET, { expiresIn: '1d' });

async function run() {
  const socket = io('http://localhost:5000', { extraHeaders: { cookie: `token=${token}` } });
  socket.on('chat:chunk', data => { 
      if (data.chunk) process.stdout.write(data.chunk);
      else console.log("\n[Empty chunk received]");
  });
  socket.on('chat:complete', data => { 
      console.log('\n\n--- COMPLETE EVENT DATA ---'); 
      console.log(JSON.stringify(data, null, 2));
      process.exit(0); 
  });
  socket.emit('chat:send', {
    message: 'Write a python script to calculate 12 * 12 and execute it using execute_python tool. Tell me the result.',
    agent: 'coding',
    model: 'auto',
    requestId: 'test_code_4'
  });
}
run();
