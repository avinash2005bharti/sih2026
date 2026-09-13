const mongoose = require("mongoose");
const Agent = require("./src/models/agent.model");
require("dotenv").config();

async function run() {
  await mongoose.connect(process.env.MONGO_URI);
  console.log("Connected to DB.");

  const agents = [
    {
      name: "General Assistant",
      slug: "general",
      type: "general",
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
      type: "coding",
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
      type: "vision",
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
      await Agent.updateOne({ slug: agent.slug }, { $set: { isActive: true, type: agent.type } });
      console.log(`Agent already exists (and set to active): ${agent.slug}`);
    }
  }

  const allAgents = await Agent.find();
  console.log("All Agents:", allAgents.map(a => a.slug));

  mongoose.disconnect();
}

run();
