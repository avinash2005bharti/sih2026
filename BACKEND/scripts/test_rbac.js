const mongoose = require('mongoose');
const Document = require('../src/models/document.model');
const User = require('../src/models/user.model');

async function testRBAC() {
  await mongoose.connect('mongodb://admin:admin@127.0.0.1:27017/sovereign_ai?authSource=admin');
  
  const admin = await User.findOne({ role: 'admin' });
  const nonAdmin1 = await User.findOne({ email: 'avinashbharti3007@gamil.com' });
  const nonAdmin2 = await User.findOne({ email: 'avinash@example.com' });

  console.log('Admin user:', admin.email, admin._id);
  console.log('Non-admin 1 (uploaded Generative AI):', nonAdmin1.email, nonAdmin1._id);
  console.log('Non-admin 2 (has no uploads):', nonAdmin2.email, nonAdmin2._id);

  // Helper simulating getDocuments filter
  async function getDocsForUser(user) {
    const isAdmin = Boolean(user.isAdmin || user.role === 'admin');
    let filter = {};
    if (!isAdmin) {
      const adminUsers = await User.find({
        $or: [{ isAdmin: true }, { role: 'admin' }]
      }).select('_id');
      const adminIds = adminUsers.map(u => u._id);
      filter = {
        $or: [
          { uploadedBy: user._id },
          { isUploadedByAdmin: true },
          { uploadedBy: { $in: adminIds } },
          { uploadedBy: { $exists: false } },
          { uploadedBy: null }
        ]
      };
    }
    const docs = await Document.find(filter).lean();
    return docs.map(d => ({ name: d.name, isUploadedByAdmin: d.isUploadedByAdmin, uploadedBy: d.uploadedBy }));
  }

  const adminDocs = await getDocsForUser(admin);
  console.log('\n=== Admin sees ' + adminDocs.length + ' documents ===');
  adminDocs.forEach(d => console.log(' - ' + d.name + ' (byAdmin: ' + d.isUploadedByAdmin + ', uploader: ' + d.uploadedBy + ')'));

  const nonAdmin1Docs = await getDocsForUser(nonAdmin1);
  console.log('\n=== Non-Admin 1 (' + nonAdmin1.email + ') sees ' + nonAdmin1Docs.length + ' documents ===');
  nonAdmin1Docs.forEach(d => console.log(' - ' + d.name + ' (byAdmin: ' + d.isUploadedByAdmin + ', uploader: ' + d.uploadedBy + ')'));

  const nonAdmin2Docs = await getDocsForUser(nonAdmin2);
  console.log('\n=== Non-Admin 2 (' + nonAdmin2.email + ') sees ' + nonAdmin2Docs.length + ' documents ===');
  nonAdmin2Docs.forEach(d => console.log(' - ' + d.name + ' (byAdmin: ' + d.isUploadedByAdmin + ', uploader: ' + d.uploadedBy + ')'));

  await mongoose.disconnect();
  process.exit(0);
}
testRBAC().catch(e => { console.error(e); process.exit(1); });
