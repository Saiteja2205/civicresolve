import api from "./api";


export async function getComplaints() {
  const response = await api.get(
    "/complaints/",
  );

  return response.data;
}


export async function getComplaint(
  complaintId,
) {
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


export async function getComplaintAssignments(
  complaintId,
) {
  const response = await api.get(
    `/assignments/?complaint=${complaintId}`,
  );

  return response.data;
}


export async function getCategories() {
  const response = await api.get(
    "/organizations/categories/",
  );

  return response.data;
}


export async function getDepartments() {
  const response = await api.get(
    "/organizations/departments/",
  );

  return response.data;
}


export async function getOfficers(
  departmentId = "",
) {
  const endpoint = departmentId
    ? `/organizations/officers/?department=${departmentId}`
    : "/organizations/officers/";

  const response = await api.get(
    endpoint,
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


export async function assignComplaint(
  complaintId,
  assignmentData,
) {
  const response = await api.post(
    `/complaints/${complaintId}/assign/`,
    assignmentData,
  );

  return response.data;
}


export async function acknowledgeComplaint(
  complaintId,
  comment = "",
) {
  const response = await api.post(
    `/complaints/${complaintId}/acknowledge/`,
    comment.trim()
      ? { comment: comment.trim() }
      : {},
  );

  return response.data;
}


export async function startComplaint(
  complaintId,
  comment = "",
) {
  const response = await api.post(
    `/complaints/${complaintId}/start/`,
    comment.trim()
      ? { comment: comment.trim() }
      : {},
  );

  return response.data;
}


export async function resolveComplaint(
  complaintId,
  comment = "",
) {
  const response = await api.post(
    `/complaints/${complaintId}/resolve/`,
    comment.trim()
      ? { comment: comment.trim() }
      : {},
  );

  return response.data;
}


export async function closeComplaint(
  complaintId,
  comment = "",
) {
  const response = await api.post(
    `/complaints/${complaintId}/close/`,
    comment.trim()
      ? { comment: comment.trim() }
      : {},
  );

  return response.data;
}