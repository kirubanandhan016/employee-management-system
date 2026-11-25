import api from "./api";

export const employeeService = {
  async list(params) {
    const { data } = await api.get("/employees", { params });
    return data;
  },
  async getById(id) {
    const { data } = await api.get(`/employees/${id}`);
    return data;
  },
  async getMe() {
    const { data } = await api.get("/employees/me");
    return data;
  },
  async updateMe(payload) {
    const { data } = await api.patch("/employees/me", payload);
    return data;
  },
  async create(payload) {
    const { data } = await api.post("/employees", payload);
    return data;
  },
  async update(id, payload) {
    const { data } = await api.put(`/employees/${id}`, payload);
    return data;
  },
  async deactivate(id) {
    const { data } = await api.post(`/employees/${id}/deactivate`);
    return data;
  },
  async remove(id) {
    const { data } = await api.delete(`/employees/${id}`);
    return data;
  },
};
