import api from "./api";

export const authService = {
  async login(credentials) {
    const { data } = await api.post("/auth/login", credentials);
    return data;
  },
  async register(payload) {
    const { data } = await api.post("/auth/register", payload);
    return data;
  },
  async logout() {
    const { data } = await api.post("/auth/logout");
    return data;
  },
  async getMe() {
    const { data } = await api.get("/auth/me");
    return data;
  },
  async changePassword(payload) {
    const { data } = await api.post("/auth/change-password", payload);
    return data;
  },
  async listUsers(params) {
    const { data } = await api.get("/users", { params });
    return data;
  },
  async createUser(payload) {
    const { data } = await api.post("/users", payload);
    return data;
  },
  async updateUser(userId, payload) {
    const { data } = await api.patch(`/users/${userId}`, payload);
    return data;
  },
};
