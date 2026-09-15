import api from "./api.js";


export async function getNotifications() {
  const response = await api.get("/notifications/");

  return response.data;
}


export async function markNotificationRead(
  notificationId
) {
  const response = await api.post(
    `/notifications/${notificationId}/read/`
  );

  return response.data;
}


export async function markAllNotificationsRead() {
  const response = await api.post(
    "/notifications/read-all/"
  );

  return response.data;
}