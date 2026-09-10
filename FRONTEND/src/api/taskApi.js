import client from './client';

export const taskApi = {
  // Get all agentic tasks
  getTasks: async () => {
    const res = await client.get('/tasks');
    return res.data;
  },

  // Get task with detailed step-by-step executions & audit logs
  getTaskById: async (taskId) => {
    const res = await client.get(`/tasks/${taskId}`);
    return res.data;
  },

  // Create/queue an agentic task
  createTask: async (taskData) => {
    const res = await client.post('/tasks', taskData);
    return res.data;
  },

  // Cancel running or queued task
  cancelTask: async (taskId) => {
    const res = await client.patch(`/tasks/${taskId}/cancel`);
    return res.data;
  },
};

export default taskApi;
