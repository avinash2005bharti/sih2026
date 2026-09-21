const mongoose = require('mongoose');

async function connectDB(retries = 5, delay = 2000) {
    const primaryUri = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/sovereign_ai?authSource=admin';
    
    // Fallback URI: swap localhost <-> 127.0.0.1 if needed for Windows/Docker IPv6/IPv4 compatibility
    const fallbackUri = primaryUri.includes('localhost')
        ? primaryUri.replace('localhost', '127.0.0.1')
        : primaryUri.includes('127.0.0.1')
            ? primaryUri.replace('127.0.0.1', 'localhost')
            : null;

    if (mongoose.connection.readyState === 1) {
        return true;
    }

    const options = {
        serverSelectionTimeoutMS: 5000,
        connectTimeoutMS: 10000,
    };

    for (let attempt = 1; attempt <= retries; attempt++) {
        const targetUri = (attempt > 1 && fallbackUri && attempt % 2 === 0) ? fallbackUri : primaryUri;
        try {
            console.log(`📡 Connecting to MongoDB (Attempt ${attempt}/${retries})...`);
            await mongoose.connect(targetUri, options);
            console.log(`✅ Connected to MongoDB successfully (${mongoose.connection.host}:${mongoose.connection.port}/${mongoose.connection.name})`);
            return true;
        } catch (err) {
            console.error(`❌ MongoDB connection attempt ${attempt}/${retries} failed: ${err.message}`);
            
            // Immediately try fallback on first attempt failure if localhost was used
            if (attempt === 1 && fallbackUri && targetUri !== fallbackUri) {
                try {
                    console.log(`🔄 Attempting immediate fallback to alternate host...`);
                    await mongoose.connect(fallbackUri, options);
                    console.log(`✅ Connected to MongoDB successfully via fallback (${mongoose.connection.host}:${mongoose.connection.port}/${mongoose.connection.name})`);
                    return true;
                } catch (fallbackErr) {
                    console.error(`❌ Fallback connection also failed: ${fallbackErr.message}`);
                }
            }

            if (attempt < retries) {
                console.log(`⏳ Waiting ${delay / 1000}s before retrying...`);
                await new Promise((resolve) => setTimeout(resolve, delay));
            }
        }
    }

    console.warn(`⚠️ Warning: Could not establish MongoDB connection after ${retries} attempts.`);
    console.warn(`👉 Ensure MongoDB container is running: docker compose -f docker-compose/docker-compose.yml up -d mongodb`);
    return false;
}

// Global connection event listeners for resilience
mongoose.connection.on('disconnected', () => {
    console.warn('⚠️ MongoDB connection lost.');
});

mongoose.connection.on('reconnected', () => {
    console.log('✅ MongoDB connection restored.');
});

mongoose.connection.on('error', (err) => {
    console.error('❌ Mongoose connection error:', err.message);
});

module.exports = connectDB;