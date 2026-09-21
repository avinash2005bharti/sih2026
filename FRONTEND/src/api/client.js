import axios from 'axios';

// Base API client
// withCredentials: true ensures the httpOnly JWT cookie is transmitted across requests
const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const apiBaseURL = rawApiUrl.endsWith('/api') ? rawApiUrl : `${rawApiUrl.replace(/\/+$/, '')}/api`;

const client = axios.create({
  baseURL: apiBaseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,
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
