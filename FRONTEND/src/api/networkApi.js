import client from './client';

export const networkApi = {
  // Get sovereign air-gap metrics and proof
  getStatus: async () => {
    const res = await client.get('/network/status');
    return res.data;
  },

  // Get tamper-evident audit records
  getAudit: async (limit = 50) => {
    const res = await client.get(`/network/audit?limit=${limit}`);
    return res.data;
  },

  // Trigger test external connection to prove active block
  testEgress: async (destination = '8.8.8.8', port = 53) => {
    const res = await client.post('/network/test-egress', { destination, port });
    return res.data;
  },
};

export default networkApi;
