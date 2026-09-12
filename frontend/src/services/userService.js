import api from "./api.js";


export async function getProfile() {
  const response = await api.get(
    "/auth/profile/",
  );

  return response.data;
}


export async function updateProfile(
  profileData,
) {
  const response = await api.patch(
    "/auth/profile/",
    profileData,
  );

  return response.data;
}