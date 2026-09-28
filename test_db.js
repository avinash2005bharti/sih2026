require('dotenv').config({ path: 'BACKEND/.env' });
const mongoose = require('mongoose');

async function main() {
  const uri = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/sih2026';
  await mongoose.connect(uri);
  const users = await mongoose.connection.db.collection('users').find({}).toArray();
  console.log('USERS_COUNT:', users.length);
  users.forEach(u => console.log('USER:', u._id.toString(), u.email, u.role, u.isAdmin));
  process.exit(0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
