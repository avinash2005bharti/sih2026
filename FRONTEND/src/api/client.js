import axios from 'axios';

// Base API client
// withCredentials: true ensures the httpOnly JWT cookie is transmitted across requests
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Response interceptor for unified error formatting
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Extract backend error message if available
    const customError = {
      status: error.response?.status,
      message:
        error.response?.data?.message ||
        error.response?.data?.error ||
        error.message ||
        'An unexpected network error occurred',
      data: error.response?.data,
    };
    return Promise.reject(customError);
  }
);

export default client;
