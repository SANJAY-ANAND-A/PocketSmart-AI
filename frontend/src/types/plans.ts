import type { Product } from './catalog';

export interface SavedPlanListItem {
  id: number;
  title: string;
  module_type: string;
  total_budget: number;
  allocated_budget: number;
  remaining_budget: number;
  currency: string;
  currency_symbol: string;
  is_fallback: boolean;
  items_count: number;
  recommendations_count: number;
  created_at: string;
  updated_at: string;
}

export interface SavedPlanListResponse {
  items: SavedPlanListItem[];
  total: number;
}

export interface SavedPlanBudgetItem {
  id: number;
  category_name: string;
  allocated_amount: number;
  spent_amount: number;
  priority: string;
  reason?: string | null;
  created_at: string;
}

export interface SavedPlanRecommendation {
  id: number;
  product_id: number;
  match_score: number;
  recommendation_reason?: string | null;
  is_upgrade: boolean;
  product?: Product | null;
}

export interface SavedPlanDetailResponse {
  id: number;
  title: string;
  module_type: string;
  total_budget: number;
  allocated_budget: number;
  remaining_budget: number;
  currency: string;
  currency_symbol: string;
  is_fallback: boolean;
  preferences?: Record<string, unknown> | null;
  ai_reasoning?: string | null;
  items: SavedPlanBudgetItem[];
  recommendations: SavedPlanRecommendation[];
  created_at: string;
  updated_at: string;
}

export interface DeletePlanResponse {
  detail: string;
  plan_id: number;
}
