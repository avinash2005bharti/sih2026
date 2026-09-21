const mongoose = require('mongoose');

async function fixDocs() {
  const uri = process.env.MONGO_URI || 'mongodb://admin:admin@127.0.0.1:27017/sovereign_ai?authSource=admin';
  await mongoose.connect(uri);
  const db = mongoose.connection.db;

  // Find all admin users
  const adminUsers = await db.collection('users').find({
    $or: [{ isAdmin: true }, { role: 'admin' }]
  }).toArray();
  const adminIds = adminUsers.map(u => u._id.toString());
  console.log('Admin user IDs:', adminIds);

  const primaryAdmin = adminUsers.find(u => u.role === 'admin' || u.isAdmin) || adminUsers[0];

  const allDocs = await db.collection('documents').find({}).toArray();
  for (const d of allDocs) {
    const uploaderIdStr = d.uploadedBy ? d.uploadedBy.toString() : null;
    let isDocAdmin = false;
    let role = 'operator';
    let uploaderName = 'System';
    let uploaderEmail = '';

    if (uploaderIdStr && adminIds.includes(uploaderIdStr)) {
      isDocAdmin = true;
      role = 'admin';
      const uploader = adminUsers.find(u => u._id.toString() === uploaderIdStr);
      if (uploader) {
        uploaderName = uploader.fullName ? `${uploader.fullName.firstName || ''} ${uploader.fullName.lastName || ''}`.trim() : uploader.email;
        uploaderEmail = uploader.email || '';
      }
    } else if (!uploaderIdStr) {
      // Global system asset
      isDocAdmin = true;
      role = 'admin';
      if (primaryAdmin) {
        await db.collection('documents').updateOne({ _id: d._id }, { $set: { uploadedBy: primaryAdmin._id } });
        uploaderName = primaryAdmin.fullName ? `${primaryAdmin.fullName.firstName || ''} ${primaryAdmin.fullName.lastName || ''}`.trim() : primaryAdmin.email;
        uploaderEmail = primaryAdmin.email || '';
      }
    } else {
      const user = await db.collection('users').findOne({ _id: d.uploadedBy });
      if (user && (user.isAdmin || user.role === 'admin')) {
        isDocAdmin = true;
        role = 'admin';
      } else if (user) {
        role = user.role || 'operator';
      }
      if (user) {
        uploaderName = user.fullName ? `${user.fullName.firstName || ''} ${user.fullName.lastName || ''}`.trim() : user.email;
        uploaderEmail = user.email || '';
      }
    }

    await db.collection('documents').updateOne(
      { _id: d._id },
      {
        $set: {
          isUploadedByAdmin: isDocAdmin,
          uploaderRole: role,
          uploaderInfo: {
            name: uploaderName,
            email: uploaderEmail,
            role: role
          }
        }
      }
    );
    console.log(`Updated doc '${d.name}' (${d._id}): isUploadedByAdmin=${isDocAdmin}, uploaderRole=${role}`);
  }

  const updatedDocs = await db.collection('documents').find({}).toArray();
  console.log('--- Current DB Documents State ---');
  for (const d of updatedDocs) {
    console.log({
      id: d._id,
      name: d.name,
      uploadedBy: d.uploadedBy,
      isUploadedByAdmin: d.isUploadedByAdmin,
      uploaderRole: d.uploaderRole
    });
  }

  await mongoose.disconnect();
  process.exit(0);
}

fixDocs().catch(e => {
  console.error(e);
  process.exit(1);
});
