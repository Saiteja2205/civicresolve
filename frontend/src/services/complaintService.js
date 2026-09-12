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
  comment = "",
) {
  const response = await api.post(
    `/complaints/${complaintId}/acknowledge/`,
    {
      comment,
    },
  );

  return response.data;
}


export async function startComplaint(
  complaintId,
  comment = "",
) {
  const response = await api.post(
    `/complaints/${complaintId}/start/`,
    {
      comment,
    },
  );

  return response.data;
}


export async function resolveComplaint(
  complaintId,
  comment = "",
) {
  const response = await api.post(
    `/complaints/${complaintId}/resolve/`,
    {
      comment,
    },
  );

  return response.data;
}


export async function closeComplaint(
  complaintId,
  comment = "",
) {
  const response = await api.post(
    `/complaints/${complaintId}/close/`,
    {
      comment,
    },
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


export async function reopenComplaint(
  complaintId,
  comment,
) {
  const response = await api.post(
    `/complaints/${complaintId}/reopen/`,
    {
      comment,
    },
  );

  return response.data;
}