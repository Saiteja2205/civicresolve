import api from "./api";

export async function login(email, password) {
  const response = await api.post("/auth/token/", {
    email,
    password,
  });

  return response.data;
}

export async function refreshAccessToken(refreshToken) {
  const response = await api.post("/auth/token/refresh/", {
    refresh: refreshToken,
  });

  return response.data;
}