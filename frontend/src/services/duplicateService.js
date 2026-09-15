import api from "./api.js";


export async function getDuplicateRecords() {
  const response = await api.get(
    "/complaint-duplicates/"
  );

  return response.data;
}


export async function reviewDuplicate(
  duplicateId,
  status,
  reviewComment = ""
) {
  const response = await api.patch(
    `/complaint-duplicates/${duplicateId}/`,
    {
      status,
      review_comment: reviewComment,
    }
  );

  return response.data;
}