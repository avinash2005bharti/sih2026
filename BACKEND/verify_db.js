const mongoose = require("mongoose");
const Agent = require("c:/Users/ayush/Desktop/sih2026-main/BACKEND/src/models/agent.model");
require("dotenv").config({ path: "c:/Users/ayush/Desktop/sih2026-main/BACKEND/.env" });

async function run() {
  await mongoose.connect(process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/sovereign-ai");
  console.log("Connected to DB.");

  const agents = [
    {
      name: "General Assistant",
      slug: "general",
      role: "orchestrator",
      systemPrompt: "You are a general AI assistant...",
      capabilities: ["chat", "files"],
      modelName: "auto",
      temperature: 0.7,
      maxTokens: 2048,
      isActive: true,
    },
    {
      name: "Coding Agent",
      slug: "coding",
      role: "expert",
      systemPrompt: "You are an expert coder...",
      capabilities: ["chat", "code"],
      modelName: "auto",
      temperature: 0.2,
      maxTokens: 4096,
      isActive: true,
    },
    {
      name: "Vision Agent",
      slug: "vision",
      role: "expert",
      systemPrompt: "You are a vision AI...",
      capabilities: ["chat", "vision"],
      modelName: "auto",
      temperature: 0.4,
      maxTokens: 2048,
      isActive: true,
    }
  ];

  for (const agent of agents) {
    const exists = await Agent.findOne({ slug: agent.slug });
    if (!exists) {
      await Agent.create(agent);
      console.log(`Created agent: ${agent.slug}`);
    } else {
      await Agent.updateOne({ slug: agent.slug }, { $set: { isActive: true } });
      console.log(`Agent already exists (and set to active): ${agent.slug}`);
    }
  }

  const allAgents = await Agent.find();
  console.log("All Agents:", allAgents.map(a => a.slug));

  mongoose.disconnect();
}

run();
