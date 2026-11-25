import api from "./api";

export const leaveService = {
  async list(params) {
    const { data } = await api.get("/leaves", { params });
    return data;
  },
  async apply(payload) {
    const { data } = await api.post("/leaves", payload);
    return data;
  },
  async review(leaveId, payload) {
    const { data } = await api.patch(`/leaves/${leaveId}/review`, payload);
    return data;
  },
  async cancel(leaveId) {
    const { data } = await api.post(`/leaves/${leaveId}/cancel`);
    return data;
  },
};
