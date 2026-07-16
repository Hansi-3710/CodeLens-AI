/**
 * React Query hooks wrapping api/client.ts — pages import these, never
 * client.ts directly, so caching/loading/error state is consistent
 * everywhere.
 *
 * Belongs to: frontend/src/api/
 * Phase: 7 (Frontend)
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as api from "./client";
import type { PromptInput } from "../types";

export function useModels() {
  return useQuery({ queryKey: ["models"], queryFn: api.listModels });
}

export function useExperiments() {
  return useQuery({ queryKey: ["experiments"], queryFn: api.listExperiments });
}

export function useExperiment(id: string | undefined) {
  return useQuery({
    queryKey: ["experiment", id],
    queryFn: () => api.getExperiment(id!),
    enabled: !!id,
    // Poll while generation is running so the UI reflects status without a manual refresh.
    refetchInterval: (query) => (query.state.data?.status === "running" ? 2000 : false),
  });
}

export function useCreateExperiment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, prompts, models }: { name: string; prompts: PromptInput[]; models: string[] }) =>
      api.createExperiment(name, prompts, models),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["experiments"] }),
  });
}

export function useGenerate(experimentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.generateSolutions(experimentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["experiment", experimentId] });
      queryClient.invalidateQueries({ queryKey: ["results", experimentId] });
    },
  });
}

export function useResults(experimentId: string | undefined) {
  return useQuery({
    queryKey: ["results", experimentId],
    queryFn: () => api.getResults(experimentId!),
    enabled: !!experimentId,
  });
}

export function useSolutions(experimentId: string | undefined) {
  return useQuery({
    queryKey: ["solutions", experimentId],
    queryFn: () => api.listSolutions(experimentId!),
    enabled: !!experimentId,
  });
}

export function useAnalytics(experimentId: string | undefined) {
  return useQuery({
    queryKey: ["analytics", experimentId],
    queryFn: () => api.getAnalytics(experimentId!),
    enabled: !!experimentId,
  });
}

export function useSimilarity(experimentId: string | undefined) {
  return useQuery({
    queryKey: ["similarity", experimentId],
    queryFn: () => api.getSimilarity(experimentId!),
    enabled: !!experimentId,
  });
}

export function useClusters(experimentId: string | undefined) {
  return useQuery({
    queryKey: ["clusters", experimentId],
    queryFn: () => api.getClusters(experimentId!),
    enabled: !!experimentId,
  });
}
