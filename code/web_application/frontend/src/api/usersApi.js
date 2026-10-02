import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8044",
  withCredentials: true,
});

export async function fetchVulnerabilities() {
  const res = await api.get("/api/vulnerabilities");
  return res.data;
}

export async function fetchVulnerabilityById(id) {
  const res = await api.get(`/api/vulnerabilities/${id}`);
  return res.data;
}

export async function createVulnerability(payload) {
  const res = await api.post("/api/vulnerabilities", payload);
  return res.data;
}

export async function updateVulnerability(id, payload) {
  const res = await api.put(`/api/vulnerabilities/${id}`, payload);
  return res.data;
}

export async function deleteVulnerability(id) {
  const res = await api.delete(`/api/vulnerabilities/${id}`);
  return res.data;
}

export async function login(email, password) {
  const res = await api.post(`/auth/login`, {email, password});
  return res.data;
}

export async function logout() {
  const res = await api.post("/auth/logout");
  return res.data;
}

export async function me() {
  const res = await api.get("/auth/me");
  return res.data;
}