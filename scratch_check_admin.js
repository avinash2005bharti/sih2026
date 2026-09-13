const mongoose = require('mongoose');
const User = require('./src/models/user.model.js');

async function run() {
  await mongoose.connect(process.env.MONGO_URI);
  const users = await User.find({});
  console.log("Users:", users.map(u => ({ id: u._id, email: u.email, role: u.role })));
  process.exit(0);
}
run();
