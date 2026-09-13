// Seed script to ensure required agents exist
// Run with: node src/seed/seedAgents.js
const mongoose = require('mongoose');
const Agent = require('../models/agent.model');
require('dotenv').config({ path: '../../.env' });

const mongoUri = process.env.MONGO_URI || 'mongodb://localhost:27017/sovereign';

mongoose.connect(mongoUri, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(async () => {
    console.log('Connected to MongoDB for seeding agents');
    // Ensure a "general" agent exists
    const existing = await Agent.findOne({ slug: 'general' });
    if (!existing) {
      const generalAgent = new Agent({
        name: 'General',
        slug: 'general',
        type: 'custom',
        systemPrompt: 'You are a helpful assistant.',
      });
      await generalAgent.save();
      console.log('Created general agent');
    } else {
      console.log('General agent already exists');
    }
    process.exit(0);
  })
  .catch(err => {
    console.error('Seeding error:', err);
    process.exit(1);
  });
