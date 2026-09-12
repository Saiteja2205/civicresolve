import api from "./api";

export async function getComplaints() {
  const response = await api.get("/complaints/");
  return response.data;
}

export async function getComplaint(complaintId) {
  const response = await api.get(
    `/complaints/${complaintId}/`,
  );

  return response.data;
}

export async function getComplaintHistory(
  complaintId,
) {
  const response = await api.get(
    `/complaints/${complaintId}/history/`,
  );

  return response.data;
}

export async function getCategories() {
  const response = await api.get(
    "/organizations/categories/",
  );

  return response.data;
}

export async function createComplaint(
  complaintData,
) {
  const response = await api.post(
    "/complaints/",
    complaintData,
  );

  return response.data;
}