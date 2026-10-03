import React, { useCallback, useEffect, useState } from 'react';
import {
  ShoppingBag,
  Search,
  Filter,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { catalogService } from '../services/catalogService';
import type { Category, Product } from '../types/catalog';
import { ProductCard } from '../components/ProductCard';
import { Toast } from '../components/Toast';

const VENDORS = [
  'All Vendors',
  'Amazon',
  'Flipkart',
  'IKEA',
  'Swiggy',
  'Zomato',
  'OYO',
  'Local',
];

export const CatalogPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);

  // Filter state
  const [activeModule, setActiveModule] = useState<'all' | 'home' | 'party' | 'jewelry'>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedVendor, setSelectedVendor] = useState<string>('All Vendors');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load categories once
  useEffect(() => {
    async function loadCategories() {
      try {
        const cats = await catalogService.getCategories();
        setCategories(cats);
      } catch {
        // Non-blocking error
      }
    }
    loadCategories();
  }, []);

  const fetchProducts = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const params: Record<string, string | number> = {
        limit: 100, // Fetch up to 100 items to display full catalog
      };

      if (activeModule !== 'all') {
        params.module = activeModule;
      }
      if (searchQuery.trim()) {
        params.search = searchQuery.trim();
      }
      if (selectedVendor !== 'All Vendors') {
        params.vendor = selectedVendor;
      }
      if (selectedCategory !== 'all') {
        params.category = selectedCategory;
      }
      if (minPrice && Number(minPrice) >= 0) {
        params.min_price = Number(minPrice);
      }
      if (maxPrice && Number(maxPrice) > 0) {
        params.max_price = Number(maxPrice);
      }

      const res = await catalogService.getProducts(params);
      setProducts(res.items);
      setTotalCount(res.total);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve catalog products.';
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  }, [activeModule, searchQuery, selectedVendor, selectedCategory, minPrice, maxPrice]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProducts();
    }, 250);
    return () => clearTimeout(timer);
  }, [fetchProducts]);

  const handleResetFilters = () => {
    setActiveModule('all');
    setSearchQuery('');
    setSelectedVendor('All Vendors');
    setSelectedCategory('all');
    setMinPrice('');
    setMaxPrice('');
  };

  // Filter category dropdown items based on active module
  const filteredCategories = categories.filter((c) =>
    activeModule === 'all' ? true : c.module_type === activeModule
  );

  return (
    <div className="catalog-page-container">
      {/* Page Header */}
      <div className="view-header">
        <span className="view-badge catalog">
          <ShoppingBag size={13} /> Product & Services Catalog
        </span>
        <h1 className="view-title">Cross-Platform Recommendation Catalog</h1>
        <p className="view-subtitle">
          Explore {totalCount} curated demo products and services across Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, and Local Indian artisans.
        </p>
      </div>

      {errorMsg && <Toast type="error" message={errorMsg} onClose={() => setErrorMsg(null)} />}

      {/* Module Navigation Tabs */}
      <div className="catalog-module-tabs">
        <button
          type="button"
          className={`module-tab ${activeModule === 'all' ? 'active' : ''}`}
          onClick={() => {
            setActiveModule('all');
            setSelectedCategory('all');
          }}
        >
          All Domains
        </button>
        <button
          type="button"
          className={`module-tab ${activeModule === 'home' ? 'active' : ''}`}
          onClick={() => {
            setActiveModule('home');
            setSelectedCategory('all');
          }}
        >
          Home Interior
        </button>
        <button
          type="button"
          className={`module-tab ${activeModule === 'party' ? 'active' : ''}`}
          onClick={() => {
            setActiveModule('party');
            setSelectedCategory('all');
          }}
        >
          Party & Events
        </button>
        <button
          type="button"
          className={`module-tab ${activeModule === 'jewelry' ? 'active' : ''}`}
          onClick={() => {
            setActiveModule('jewelry');
            setSelectedCategory('all');
          }}
        >
          Jewelry
        </button>
      </div>

      {/* Search and Filter Toolbar */}
      <div className="catalog-toolbar">
        <div className="search-bar-wrapper">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search products by keyword, style, tags, or platform..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-dropdowns-row">
          {/* Vendor Dropdown */}
          <div className="dropdown-wrapper">
            <select
              className="filter-select"
              value={selectedVendor}
              onChange={(e) => setSelectedVendor(e.target.value)}
            >
              {VENDORS.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>

          {/* Category Dropdown */}
          <div className="dropdown-wrapper">
            <select
              className="filter-select"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              {filteredCategories.map((c) => (
                <option key={c.id} value={c.slug}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Price Range */}
          <div className="price-inputs-row">
            <input
              type="number"
              placeholder="Min ₹"
              className="price-filter-input"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
            />
            <span className="price-dash">—</span>
            <input
              type="number"
              placeholder="Max ₹"
              className="price-filter-input"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
            />
          </div>

          {/* Reset Filters */}
          <button
            type="button"
            className="btn-reset-filters"
            onClick={handleResetFilters}
            title="Reset filters"
          >
            <RotateCcw size={15} />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Results Header Count */}
      <div className="catalog-results-header">
        <span className="results-count">
          Showing <strong>{products.length}</strong> items in catalog
        </span>
        <div className="catalog-note-pill">
          <Sparkles size={13} />
          <span>Used by Gemini recommendation algorithms</span>
        </div>
      </div>

      {/* Products Grid */}
      {isLoading ? (
        <div className="catalog-loading-state">
          <span className="btn-spinner">Filtering catalog...</span>
        </div>
      ) : products.length === 0 ? (
        <div className="catalog-empty-card">
          <Filter size={36} className="empty-filter-icon" />
          <h3>No Matching Catalog Items</h3>
          <p>Try clearing your search query or loosening your price filter limits.</p>
          <button type="button" className="btn-secondary" onClick={handleResetFilters}>
            Reset All Filters
          </button>
        </div>
      ) : (
        <div className="catalog-products-grid">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}
    </div>
  );
};
