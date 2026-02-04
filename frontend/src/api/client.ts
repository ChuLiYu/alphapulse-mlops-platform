import axios from "axios";
import { SERVICE_URLS } from "../config/links-runtime";

const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// Add a request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // If Demo Mode is enabled, we could potentially intercept here,
    // but for now we'll handle it in the response interceptor or by letting it fail
    // and using fallbacks in hooks.
    return config;
  },
  (error) => Promise.reject(error)
);

// Add a response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // If Demo Mode is enabled, we return a resolved promise for certain endpoints
    // to simulate a working system even if the backend is down.
    if (SERVICE_URLS.IS_DEMO_MODE) {
      console.warn(`[Demo Mode] Intercepted failed request to ${error.config.url}. Returning mock success.`);
      
      // Return a simulated successful response structure
      return {
        data: {
          success: true,
          data: [], // Handled by individual component fallbacks
          message: "Demo Mode Active"
        },
        status: 200,
        statusText: "OK",
        headers: {},
        config: error.config,
      };
    }
    return Promise.reject(error);
  }
);

export default apiClient;
