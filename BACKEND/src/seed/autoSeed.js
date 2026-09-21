const Agent = require('../models/agent.model');
const AIModel = require('../models/aiModel.model');
const User = require('../models/user.model');
const bcrypt = require('bcrypt');

async function seedDefaultModels() {
    const modelsToSeed = [
        {
            name: 'qwen2.5:1.5b',
            displayName: 'Qwen 2.5 (1.5B)',
            provider: 'ollama',
            modelType: 'llm',
            capabilities: ['text', 'reasoning', 'multilingual'],
            contextWindow: 32768,
            isLocal: true,
            isActive: true,
            priority: 10
        },
        {
            name: 'qwen2.5-coder:1.5b',
            displayName: 'Qwen 2.5 Coder (1.5B)',
            provider: 'ollama',
            modelType: 'llm',
            capabilities: ['text', 'coding', 'reasoning'],
            contextWindow: 32768,
            isLocal: true,
            isActive: true,
            priority: 9
        },
        {
            name: 'moondream',
            displayName: 'Moondream 2 Vision',
            provider: 'ollama',
            modelType: 'vision',
            capabilities: ['vision', 'document'],
            contextWindow: 8192,
            isLocal: true,
            isActive: true,
            priority: 8
        },
        {
            name: 'paddleocr',
            displayName: 'PaddleOCR Engine',
            provider: 'local',
            modelType: 'ocr',
            capabilities: ['ocr'],
            contextWindow: 4096,
            isLocal: true,
            isActive: true,
            priority: 8
        },
        {
            name: 'qwen2.5vl:3b',
            displayName: 'Qwen 2.5 VL (3B)',
            provider: 'ollama',
            modelType: 'vlm',
            capabilities: ['text', 'vision', 'document'],
            contextWindow: 32768,
            isLocal: true,
            isActive: true,
            priority: 7
        },
        {
            name: 'nomic-embed-text:latest',
            displayName: 'Nomic Embed Text',
            provider: 'ollama',
            modelType: 'embedding',
            capabilities: ['embedding'],
            contextWindow: 8192,
            isLocal: true,
            isActive: true,
            priority: 7
        }
    ];

    for (const modelData of modelsToSeed) {
        const existing = await AIModel.findOne({ name: modelData.name });
        if (!existing) {
            await AIModel.create(modelData);
            console.log(`Successfully created default model: ${modelData.name}`);
        }
    }
}

async function seedDefaultAdmin() {
    try {
        const userCount = await User.countDocuments();
        if (userCount === 0) {
            const hashedPassword = await bcrypt.hash('Admin@12345', 10);
            await User.create({
                fullName: {
                    firstName: 'Sovereign',
                    lastName: 'Administrator'
                },
                email: 'admin@sovereign.local',
                password: hashedPassword,
                role: 'admin',
                isAdmin: true,
                isActive: true,
                department: 'Cyber Operations'
            });
            console.log('✅ Created default administrator account: admin@sovereign.local / Admin@12345');
        }
    } catch (err) {
        console.error('Error seeding default admin user:', err.message);
    }
}

async function seedDefaultAgents() {
    try {
        await seedDefaultModels();
        await seedDefaultAdmin();

        // 1. General Agent
        const generalExisting = await Agent.findOne({ slug: 'general' });
        const generalPrompt = `You are a helpful, accurate, and versatile AI assistant for the Sovereign AI Workbench. You operate entirely within the organization's secure on-premise environment. You have full visibility into the workspace document repository, files, and local tools. You can track, count, list, inspect, and analyze documents in the workspace. Never claim that you cannot track or view documents in the workspace. Never expose confidential credentials or internal configuration.`;
        if (!generalExisting) {
            await Agent.create({
                name: 'General Assistant',
                slug: 'general',
                type: 'orchestrator',
                description: 'General purpose AI assistant for conversation, reasoning, and technical assistance.',
                systemPrompt: generalPrompt,
                temperature: 0.7,
                maxTokens: 4096,
                modelName: 'qwen2.5:1.5b',
                capabilities: ['conversation', 'reasoning', 'technical_assistance', 'document_management'],
                isActive: true
            });
            console.log("Successfully created default 'general' agent.");
        } else {
            await Agent.updateOne({ slug: 'general' }, { modelName: 'qwen2.5:1.5b', systemPrompt: generalPrompt });
        }

        // 2. Coding Agent
        const codingExisting = await Agent.findOne({ slug: 'coding' });
        if (!codingExisting) {
            await Agent.create({
                name: 'Coding Assistant',
                slug: 'coding',
                type: 'coding',
                description: 'Expert coding assistant with access to file management and execution tools.',
                systemPrompt: `You are an expert coding assistant for the Sovereign AI Workbench. You can write, edit, run, and debug code. You prioritize clean, secure, and well-documented code.`,
                temperature: 0.2,
                maxTokens: 8192,
                modelName: 'qwen2.5-coder:1.5b',
                capabilities: ['coding', 'reasoning'],
                isActive: true
            });
            console.log("Successfully created default 'coding' agent.");
        } else {
            await Agent.updateOne({ slug: 'coding' }, { modelName: 'qwen2.5-coder:1.5b' });
        }

        // 3. Vision Agent
        const visionExisting = await Agent.findOne({ slug: 'vision' });
        if (!visionExisting) {
            await Agent.create({
                name: 'Vision Assistant',
                slug: 'vision',
                type: 'vision',
                description: 'Multimodal assistant capable of understanding images, diagrams, and scanned documents.',
                systemPrompt: `You are a specialized vision assistant for the Sovereign AI Workbench. You excel at extracting information from images, UI mockups, and diagrams.`,
                temperature: 0.4,
                maxTokens: 4096,
                modelName: 'qwen2.5vl:3b',
                capabilities: ['vision', 'document', 'reasoning'],
                isActive: true
            });
            console.log("Successfully created default 'vision' agent.");
        } else {
            await Agent.updateOne({ slug: 'vision' }, { modelName: 'qwen2.5vl:3b' });
        }

    } catch (error) {
        console.error("Error seeding default agents/models:", error);
    }
}

module.exports = { seedDefaultAgents, seedDefaultAdmin };
