import React from 'react';
import { Star, ExternalLink, Sparkles, CheckCircle2 } from 'lucide-react';
import type { Product } from '../types/catalog';
import { formatINR } from '../utils/formatters';

interface ProductCardProps {
  product: Product;
  quantity?: number;
  subtotal?: number;
  reason?: string;
  matchScore?: number;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  quantity,
  subtotal,
  reason,
  matchScore,
}) => {
  // Normalize platform badge styling
  const platform = product.platform.toLowerCase();
  let platformClass = 'platform-default';
  if (platform.includes('ikea')) platformClass = 'platform-ikea';
  else if (platform.includes('amazon')) platformClass = 'platform-amazon';
  else if (platform.includes('flipkart')) platformClass = 'platform-flipkart';
  else if (platform.includes('swiggy')) platformClass = 'platform-swiggy';
  else if (platform.includes('zomato')) platformClass = 'platform-zomato';
  else if (platform.includes('oyo')) platformClass = 'platform-oyo';
  else if (platform.includes('local')) platformClass = 'platform-local';

  return (
    <div className="product-card">
      {/* Top Meta: Platform Badge & Category */}
      <div className="product-card-header">
        <span className={`platform-badge ${platformClass}`}>
          {product.platform}
        </span>

        <div className="header-meta-right">
          {product.category_name && (
            <span className="category-pill">{product.category_name}</span>
          )}
          {product.rating > 0 && (
            <span className="rating-pill">
              <Star size={12} className="star-icon" fill="currentColor" />
              {product.rating.toFixed(1)}
            </span>
          )}
        </div>
      </div>

      {/* Main Info */}
      <div className="product-card-body">
        <h4 className="product-name" title={product.name}>
          {product.name}
        </h4>

        {product.description && (
          <p className="product-description">{product.description}</p>
        )}

        {/* Tags or Style if available */}
        <div className="product-tags-row">
          {product.subcategory && (
            <span className="tag-pill">{product.subcategory}</span>
          )}
          {product.style && (
            <span className="tag-pill style">{product.style}</span>
          )}
          {product.is_demo && (
            <span className="tag-pill demo">Sample Catalog</span>
          )}
        </div>

        {/* AI Recommendation Reason */}
        {reason && (
          <div className="recommendation-reason-box">
            <Sparkles size={14} className="reason-sparkle" />
            <span className="reason-text">{reason}</span>
          </div>
        )}
      </div>

      {/* Pricing & Quantity Footer */}
      <div className="product-card-footer">
        <div className="price-stack">
          {quantity && quantity > 1 ? (
            <>
              <span className="unit-price">
                {formatINR(product.price)} × {quantity}
              </span>
              <span className="total-price">{formatINR(subtotal ?? product.price * quantity)}</span>
            </>
          ) : (
            <span className="total-price">{formatINR(product.price)}</span>
          )}
        </div>

        {matchScore !== undefined && matchScore > 0 && (
          <span className="match-score-badge" title="AI Preference Fit Score">
            <CheckCircle2 size={13} /> {(matchScore * 100).toFixed(0)}% Match
          </span>
        )}

        {product.product_url ? (
          <a
            href={product.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-product-link"
            title="View on platform"
          >
            <span>View</span>
            <ExternalLink size={13} />
          </a>
        ) : (
          <span className="vendor-name-hint" title={product.vendor_name || ''}>
            {product.vendor_name || product.platform}
          </span>
        )}
      </div>
    </div>
  );
};
