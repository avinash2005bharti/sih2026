import re

with open("BACKEND/src/sockets/socket.server.js", "r", encoding="utf-8") as f:
    text = f.read()

replacement = """const activeGenerations = new Map();

module.exports = function initializeSocketServer(httpServer) {
  const io = new Server(httpServer, {
    cors: {
      origin: process.env.FRONTEND_URL || "http://localhost:5173",
      credentials: true,
      methods: ["GET", "POST"],
    },
    transports: ["websocket", "polling"],
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
      
      socket.userId = decoded.id;
      socket.user = await userModel.findById(decoded.id);

      if (!socket.user) {
        return next(new Error("User not found"));
      }

      next();
    } catch (error) {
      console.error("❌ Socket Auth Error:", error.message);
      next(new Error("Authentication failed"));
    }
  });

  io.on("connection", async (socket) => {
    console.log(`✅ Client connected: ${socket.id} (User: ${socket.user.email})`);
    socket.join(`user:${socket.userId}`);
    socket.emit("socket:connected\""""

text = re.sub(r'const activeGenerations = new Map\(\);\n+.*?socket\.emit\("socket:connected"', replacement, text, flags=re.DOTALL)

with open("BACKEND/src/sockets/socket.server.js", "w", encoding="utf-8") as f:
    f.write(text)
