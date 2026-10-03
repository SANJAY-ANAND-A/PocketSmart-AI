export interface Category {
  id: number;
  name: string;
  slug: string;
  module_type: string;
  description?: string | null;
  icon?: string | null;
}

export interface Vendor {
  id: number;
  name: string;
  platform: string;
  description?: string | null;
  rating: number;
  website_url?: string | null;
  is_demo: boolean;
}

export interface Product {
  id: number;
  name: string;
  description?: string | null;
  price: number;
  currency: string;
  currency_symbol: string;
  category_id: number;
  category_name?: string | null;
  module_type?: string | null;
  subcategory?: string | null;
  platform: string;
  vendor_id?: number | null;
  vendor_name?: string | null;
  rating: number;
  image_url?: string | null;
  product_url?: string | null;
  tags?: string | null;
  style?: string | null;
  availability: boolean;
  is_demo: boolean;
  created_at: string;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  limit: number;
  offset: number;
  currency: string;
  currency_symbol: string;
}

export interface ProductFilterParams {
  module?: string;
  category?: string;
  vendor?: string;
  min_price?: number;
  max_price?: number;
  search?: string;
  style?: string;
  limit?: number;
  offset?: number;
}
