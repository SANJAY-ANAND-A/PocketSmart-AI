import { apiClient } from './api';
import type { DeletePlanResponse, SavedPlanDetailResponse, SavedPlanListResponse } from '../types/plans';

export const plansService = {
  async getPlans(module?: string): Promise<SavedPlanListResponse> {
    const endpoint = module ? `/plans?module=${encodeURIComponent(module)}` : '/plans';
    return apiClient<SavedPlanListResponse>(endpoint, { method: 'GET' });
  },

  async getPlanDetail(id: number): Promise<SavedPlanDetailResponse> {
    return apiClient<SavedPlanDetailResponse>(`/plans/${id}`, { method: 'GET' });
  },

  async deletePlan(id: number): Promise<DeletePlanResponse> {
    return apiClient<DeletePlanResponse>(`/plans/${id}`, { method: 'DELETE' });
  },
};
