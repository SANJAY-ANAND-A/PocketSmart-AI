import { apiClient } from './api';
import type {
  HomePlanRequest,
  HomePlanResponse,
  JewelryPlanRequest,
  JewelryPlanResponse,
  PartyPlanRequest,
  PartyPlanResponse,
} from '../types/planner';

export const plannerService = {
  async planHome(data: HomePlanRequest): Promise<HomePlanResponse> {
    return apiClient<HomePlanResponse>('/planner/home', {
      method: 'POST',
      body: data,
    });
  },

  async planParty(data: PartyPlanRequest): Promise<PartyPlanResponse> {
    return apiClient<PartyPlanResponse>('/planner/party', {
      method: 'POST',
      body: data,
    });
  },

  async planJewelry(data: JewelryPlanRequest): Promise<JewelryPlanResponse> {
    // If outfit_image is provided, send as multipart/form-data via FormData
    if (data.outfit_image instanceof File) {
      const formData = new FormData();
      formData.append('budget', data.budget.toString());
      formData.append('occasion', data.occasion);
      if (data.style) formData.append('style', data.style);
      if (data.preferred_metal) formData.append('preferred_metal', data.preferred_metal);
      if (data.preferred_color) formData.append('preferred_color', data.preferred_color);
      if (data.jewelry_type) formData.append('jewelry_type', data.jewelry_type);
      if (data.preferences) formData.append('preferences', data.preferences);
      if (data.title) formData.append('title', data.title);
      formData.append('outfit_image', data.outfit_image);

      return apiClient<JewelryPlanResponse>('/planner/jewelry', {
        method: 'POST',
        body: formData,
      });
    }

    // Otherwise send as standard JSON
    const { outfit_image: _unused, ...jsonPayload } = data;
    return apiClient<JewelryPlanResponse>('/planner/jewelry', {
      method: 'POST',
      body: jsonPayload,
    });
  },
};
