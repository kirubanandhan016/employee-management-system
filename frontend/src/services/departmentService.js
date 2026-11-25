import api from "./api";

export const departmentService = {
  async list(params) {
    const { data } = await api.get("/departments", { params });
    return data;
  },
  async getById(id) {
    const { data } = await api.get(`/departments/${id}`);
    return data;
  },
  async create(payload) {
    const { data } = await api.post("/departments", payload);
    return data;
  },
  async update(id, payload) {
    const { data } = await api.put(`/departments/${id}`, payload);
    return data;
  },
  async remove(id) {
    const { data } = await api.delete(`/departments/${id}`);
    return data;
  },
  async assignEmployees(id, employeeIds) {
    const { data } = await api.post(`/departments/${id}/assign-employees`, {
      employee_ids: employeeIds,
    });
    return data;
  },
};
