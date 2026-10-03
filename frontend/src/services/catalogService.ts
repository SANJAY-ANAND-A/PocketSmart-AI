import { apiClient } from './api';
import type { Category, Product, ProductFilterParams, ProductListResponse } from '../types/catalog';

export const catalogService = {
  async getProducts(params: ProductFilterParams = {}): Promise<ProductListResponse> {
    const query = new URLSearchParams();
    if (params.module) query.append('module', params.module);
    if (params.category) query.append('category', params.category);
    if (params.vendor) query.append('vendor', params.vendor);
    if (params.min_price !== undefined) query.append('min_price', params.min_price.toString());
    if (params.max_price !== undefined) query.append('max_price', params.max_price.toString());
    if (params.search) query.append('search', params.search);
    if (params.style) query.append('style', params.style);
    if (params.limit !== undefined) query.append('limit', params.limit.toString());
    if (params.offset !== undefined) query.append('offset', params.offset.toString());

    const queryString = query.toString();
    const endpoint = queryString ? `/products?${queryString}` : '/products';
    return apiClient<ProductListResponse>(endpoint, { method: 'GET' });
  },

  async getProduct(id: number): Promise<Product> {
    return apiClient<Product>(`/products/${id}`, { method: 'GET' });
  },

  async getCategories(): Promise<Category[]> {
    return apiClient<Category[]>('/products/categories/all', { method: 'GET' });
  },
};
