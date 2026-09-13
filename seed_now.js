require('dotenv').config({ path: 'BACKEND/.env' });
const connectDB = require('./BACKEND/src/db/db');
const { seedDefaultAgents } = require('./BACKEND/src/seed/autoSeed');

async function run() {
    await connectDB();
    await seedDefaultAgents();
    console.log("Done");
    process.exit(0);
}
run();
