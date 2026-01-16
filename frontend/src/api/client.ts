import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// Add a request interceptor (Auth removed)
apiClient.interceptors.request.use(
  (config) => {
    // Auth token injection removed per user request
    return config;
  },
  (error) => Promise.reject(error)
);

// Add a response interceptor (Auth error handling removed)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // 401 handling removed
    return Promise.reject(error);
  }
);

export default apiClient;
