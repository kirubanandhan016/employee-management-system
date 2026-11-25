import api from "./api";

export const attendanceService = {
  async checkIn(payload = {}) {
    const { data } = await api.post("/attendance/check-in", payload);
    return data;
  },
  async checkOut(payload = {}) {
    const { data } = await api.post("/attendance/check-out", payload);
    return data;
  },
  async recordManual(payload) {
    const { data } = await api.post("/attendance", payload);
    return data;
  },
  async list(params) {
    const { data } = await api.get("/attendance", { params });
    return data;
  },
  async getReport(params) {
    const { data } = await api.get("/attendance/report", { params });
    return data;
  },
};
