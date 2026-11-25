import api from "./api";

export const salaryService = {
  async list(params) {
    const { data } = await api.get("/salaries", { params });
    return data;
  },
  async getSummary(params) {
    const { data } = await api.get("/salaries/summary", { params });
    return data;
  },
  async create(payload) {
    const { data } = await api.post("/salaries", payload);
    return data;
  },
  async update(id, payload) {
    const { data } = await api.put(`/salaries/${id}`, payload);
    return data;
  },
  async remove(id) {
    const { data } = await api.delete(`/salaries/${id}`);
    return data;
  },
};
