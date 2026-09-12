import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      error.userMessage =
        "Unable to connect to the server. Please check that the backend is running.";
      return Promise.reject(error);
    }

    const { status, data } = error.response;

    if (status === 401) {
      error.userMessage = "Your session has expired. Please sign in again.";
    } else if (status === 403) {
      error.userMessage =
        "You do not have permission to perform this action.";
    } else if (status === 404) {
      error.userMessage = "The requested resource could not be found.";
    } else if (status === 400) {
      if (typeof data === "object" && data !== null) {
        const messages = Object.entries(data)
          .map(([field, value]) => {
            const message = Array.isArray(value)
              ? value.join(", ")
              : String(value);

            return `${field}: ${message}`;
          })
          .join(" | ");

        error.userMessage = messages || "The submitted data is invalid.";
      } else {
        error.userMessage = "The submitted data is invalid.";
      }
    } else if (status >= 500) {
      error.userMessage =
        "The server encountered an error. Please try again later.";
    } else {
      error.userMessage =
        data?.detail || data?.message || "Something went wrong.";
    }

    return Promise.reject(error);
  }
);

export default api;