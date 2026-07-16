/**
 * Thin axios wrapper — every backend call in one place so React Query
 * hooks (hooks.ts) stay declarative and testable.
 *
 * Belongs to: frontend/src/api/
 *
 * Backend URL: in dev, VITE_API_BASE_URL is unset, so this falls back to
 * "/api", which vite.config.ts's dev-server proxy forwards to
 * localhost:8000 (avoids CORS friction locally). In production there is
 * no proxy — Vercel serves static files only — so VITE_API_BASE_URL must
 * be set to the real deployed backend's URL (e.g. the Render service URL)
 * as a build-time environment variable; the frontend then calls it
 * directly, relying on the backend's CORS config (app/config.py's
 * ALLOWED_ORIGINS) to allow the deployed frontend's origin.
 */
import axios from "axios";
import type {
  AIModel,
  AnalyticsSummary,
  ClustersResponse,
  Experiment,
  ExperimentResults,
  PromptInput,
  SimilarityMatrix,
  Solution,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function login(email: string, password: string): Promise<string> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const { data } = await axios.post(`${API_BASE_URL}/auth/login`, form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data.access_token as string;
}

export async function register(email: string, password: string): Promise<void> {
  await axios.post(`${API_BASE_URL}/auth/register`, { email, password });
}

export async function listModels(): Promise<AIModel[]> {
  const { data } = await api.get("/models");
  return data;
}

export async function createExperiment(
  name: string,
  prompts: PromptInput[],
  models: string[]
): Promise<Experiment> {
  const { data } = await api.post("/experiments", { name, prompts, models });
  return data;
}

export async function listExperiments(): Promise<Experiment[]> {
  const { data } = await api.get("/experiments");
  return data;
}

export async function getExperiment(id: string): Promise<Experiment> {
  const { data } = await api.get(`/experiments/${id}`);
  return data;
}

export async function generateSolutions(experimentId: string): Promise<{ status: string }> {
  const { data } = await api.post(`/experiments/${experimentId}/generate`);
  return data;
}

export async function listSolutions(experimentId: string): Promise<import("../types").SolutionSummary[]> {
  const { data } = await api.get(`/experiments/${experimentId}/solutions`);
  return data;
}

export async function getResults(experimentId: string): Promise<ExperimentResults> {
  const { data } = await api.get(`/experiments/${experimentId}/results`);
  return data;
}

export async function getSolution(id: string): Promise<Solution> {
  const { data } = await api.get(`/solutions/${id}`);
  return data;
}

export async function executeSolution(id: string) {
  const { data } = await api.post(`/solutions/${id}/execute`);
  return data;
}

export async function getAnalytics(experimentId: string): Promise<AnalyticsSummary> {
  const { data } = await api.get(`/analytics/${experimentId}`);
  return data;
}

export async function getSimilarity(experimentId: string): Promise<SimilarityMatrix> {
  const { data } = await api.get(`/analytics/${experimentId}/similarity`);
  return data;
}

export async function getClusters(experimentId: string): Promise<ClustersResponse> {
  const { data } = await api.get(`/analytics/${experimentId}/clusters`);
  return data;
}

export default api;
