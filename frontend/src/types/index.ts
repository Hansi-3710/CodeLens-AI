/**
 * Shared TypeScript types mirroring backend/app/database/schemas.py.
 * Belongs to: frontend/src/types/
 * Phase: 7 (Frontend) — kept in sync manually until Phase 8 adds an
 * OpenAPI-codegen step in CI.
 */
export interface Experiment {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  created_at: string;
}

export interface Solution {
  id: string;
  model_name: string;
  code: string;
  pass_rate: number | null;
  runtime_seconds: number | null;
  cyclomatic_complexity: number | null;
}

export interface ModelComparisonRow {
  model: string;
  correctness: number | null;
  correctness_ci_95: [number | null, number | null];
  avg_runtime_s: number | null;
  complexity: string | null;
  n_solutions: number;
}

export interface ExperimentResults {
  experiment_id: string;
  status: string;
  models: ModelComparisonRow[];
}

export interface DescriptiveStats {
  mean: number | null;
  median: number | null;
  stdev: number | null;
  ci_95_low: number | null;
  ci_95_high: number | null;
  n: number;
}

export interface AnalyticsSummary {
  experiment_id: string;
  n_solutions: number;
  code_length: DescriptiveStats;
  pass_rate: DescriptiveStats;
  cyclomatic_complexity: DescriptiveStats;
  correlations: {
    code_length_vs_pass_rate: { pearson_r: number | null; p_value: number | null; n: number };
  };
  model_fingerprint: {
    sufficient_data: boolean;
    cv_accuracy?: number | null;
    baseline_accuracy?: number | null;
  };
}

export interface SimilarityPair {
  prompt_id: string;
  model_a: string;
  model_b: string;
  token_similarity: number;
  ast_similarity: number;
  embedding_similarity: number | null;
}

export interface SimilarityMatrix {
  experiment_id: string;
  pairs: SimilarityPair[];
}

export interface ClusterPoint {
  solution_id: string;
  model: string;
  prompt_id: string;
  x: number;
  y: number;
  cluster: number;
}

export interface ClustersResponse {
  experiment_id: string;
  points: ClusterPoint[];
  note?: string;
}

export interface PromptInput {
  problem_statement: string;
  language?: string;
  difficulty?: string;
}

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  is_active: boolean;
}

export interface SolutionSummary {
  id: string;
  prompt_id: string;
  problem_statement: string;
  model_name: string;
  code: string;
}
