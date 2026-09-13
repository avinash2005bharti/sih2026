const fs = require('fs');
let code = fs.readFileSync('BACKEND/src/sockets/socket.server.js', 'utf-8');
const searchStr = `    transports: ["websocket", "polling"],
  });
      // Attach user info to socket`;

const replaceStr = `    transports: ["websocket", "polling"],
  });

  io.use(async (socket, next) => {
    try {
      let token = socket.handshake.auth?.token;
      if (!token) {
        token = socket.request.headers.cookie
          ?.split("; ")
          .find((c) => c.startsWith("token="))
          ?.split("=")[1];
      }

      if (!token) {
        return next(new Error("Authentication required"));
      }

      const jwt = require("jsonwebtoken");
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      
      // Attach user info to socket`;

code = code.replace(searchStr, replaceStr);
fs.writeFileSync('BACKEND/src/sockets/socket.server.js', code);
