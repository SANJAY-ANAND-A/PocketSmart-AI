"""Catalog and Recommendation Providers"""

from app.services.providers.base import BaseRecommendationProvider
from app.services.providers.local_catalog import LocalCatalogProvider
from app.services.providers.marketplace_stubs import (
    AmazonProvider,
    FlipkartProvider,
    IKEAProvider,
    SwiggyProvider,
    ZomatoProvider,
    OYOProvider,
)

__all__ = [
    "BaseRecommendationProvider",
    "LocalCatalogProvider",
    "AmazonProvider",
    "FlipkartProvider",
    "IKEAProvider",
    "SwiggyProvider",
    "ZomatoProvider",
    "OYOProvider",
]
