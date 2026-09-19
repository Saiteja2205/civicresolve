import api from "./api";

export async function login(email, password) {
  const response = await api.post("/auth/token/", {
    email,
    password,
  });

  return response.data;
}

export async function registerCitizen({
  email,
  firstName,
  lastName,
  phone,
  password,
  passwordConfirm,
}) {
  const response = await api.post("/auth/register/", {
    email,
    first_name: firstName,
    last_name: lastName,
    phone,
    password,
    password_confirm: passwordConfirm,
  });

  return response.data;
}

export async function refreshAccessToken(refreshToken) {
  const response = await api.post("/auth/token/refresh/", {
    refresh: refreshToken,
  });

  return response.data;
}

export async function getCurrentUser() {
  const response = await api.get("/auth/me/");

  return response.data;
}