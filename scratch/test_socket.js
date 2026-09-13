const { io } = require("socket.io-client");
const socket = io("http://localhost:5000");

let messageId;

socket.on("connect", () => {
    console.log("Connected to server", socket.id);
    messageId = `msg_${Date.now()}`;
    socket.emit("chat:send", {
        conversationId: null,
        message: "Hello world, what is the meaning of life?",
        model: "auto",
        agent: "general",
        requestId: messageId
    });
});

socket.on("chat:chunk", (data) => {
    console.log("chunk received");
    socket.emit("chat:stop", { requestId: messageId, conversationId: data.conversationId });
});

socket.on("chat:stopped", (data) => {
    console.log("Generation stopped:", data);
    process.exit(0);
});

socket.on("chat:error", (err) => {
    console.error("Error", err);
    process.exit(1);
});

socket.on("disconnect", () => {
    console.log("Disconnected");
});
