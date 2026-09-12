import api from "./api.js";


export async function getComplaints(params = {}) {
  const response = await api.get(
    "/complaints/",
    {
      params,
    },
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
    "/assignments/",
    {
      params: {
        complaint: complaintId,
      },
    },
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
  departmentId = null,
) {
  const params = {};

  if (departmentId) {
    params.department = departmentId;
  }

  const response = await api.get(
    "/organizations/officers/",
    {
      params,
    },
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
) {
  const response = await api.post(
    `/complaints/${complaintId}/acknowledge/`,
  );

  return response.data;
}


export async function startComplaint(
  complaintId,
) {
  const response = await api.post(
    `/complaints/${complaintId}/start/`,
  );

  return response.data;
}


export async function resolveComplaint(
  complaintId,
) {
  const response = await api.post(
    `/complaints/${complaintId}/resolve/`,
  );

  return response.data;
}


export async function closeComplaint(
  complaintId,
) {
  const response = await api.post(
    `/complaints/${complaintId}/close/`,
  );

  return response.data;
}


export async function getSLARecords(
  params = {},
) {
  const response = await api.get(
    "/sla/",
    {
      params,
    },
  );

  return response.data;
}