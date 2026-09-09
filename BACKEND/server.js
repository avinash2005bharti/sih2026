require('dotenv').config();
const app = require('./src/app');
const connectDB = require('./src/db/db');
const socket = require('./src/sockets/socket.server')
const httpserver = require("http").createServer(app);

connectDB();
// socket(httpserver);

httpserver.listen(5000,()=>{
    console.log("Server is running on port 5000");
});