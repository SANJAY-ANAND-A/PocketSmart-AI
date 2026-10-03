# PocketSmart AI - Database Architecture & Schema Specification

## Database Engine
- **Local Development:** SQLite (`sqlite:///./pocketsmart.db`)
- **Production Target:** PostgreSQL (via SQLAlchemy ORM abstraction)

---

## Entity Relationship Overview

```mermaid
erDiagram
    User ||--o{ BudgetPlan : "creates"
    BudgetPlan ||--|{ BudgetItem : "contains"
    BudgetPlan ||--o{ Recommendation : "generates"
    Category ||--o{ Product : "classifies"
    Vendor ||--o{ Product : "provides"
    Product ||--o{ Recommendation : "recommended_in"

    User {
        int id PK
        string email UK
        string username UK
        string hashed_password
        string full_name
        boolean is_active
        boolean is_superuser
        datetime created_at
        datetime updated_at
    }

    Vendor {
        int id PK
        string name
        string platform
        text description
        string contact_email
        float rating
        string website_url
        boolean is_demo
        datetime created_at
    }

    Category {
        int id PK
        string name
        string slug UK
        string module_type
        text description
        string icon
        datetime created_at
    }

    Product {
        int id PK
        string name
        text description
        int category_id FK
        string subcategory
        string platform
        int vendor_id FK
        float price
        float rating
        string image_url
        string product_url
        string tags
        string style
        boolean availability
        boolean is_demo
        datetime created_at
    }

    BudgetPlan {
        int id PK
        int user_id FK
        string title
        string module_type
        float total_budget
        float allocated_budget
        float remaining_budget
        string currency
        text preferences
        text ai_reasoning
        boolean is_fallback
        datetime created_at
        datetime updated_at
    }

    BudgetItem {
        int id PK
        int plan_id FK
        string category_name
        float allocated_amount
        float spent_amount
        string priority
        text reason
        datetime created_at
    }

    Recommendation {
        int id PK
        int plan_id FK
        int product_id FK
        float match_score
        text score_breakdown
        text recommendation_reason
        boolean is_upgrade
        datetime created_at
    }
```

---

## Seed Data Summary
Seeded via `python -m app.seed`:
- **7 Vendors**: IKEA (IKEA), Amazon India (Amazon), Flipkart (Flipkart), Swiggy (Swiggy), Zomato (Zomato), OYO (OYO), Local Heritage Crafts (Local).
- **22 Categories**:
  - *Home Interior (9)*: Bed, Sofa, Wardrobe, Table, Chair, Lighting, Curtains, Decor, Storage.
  - *Party / Event (7)*: Food, Venue, Decoration, Entertainment, Photography, Transportation, Miscellaneous.
  - *Jewelry (6)*: Necklace, Earrings, Bracelet, Ring, Pendant, Bangles.
- **33 Sample Products**: Realistic Indian Rupee (₹) pricing, clearly marked with `is_demo = True`.

---

## Provider Adapter Pattern
- `BaseRecommendationProvider`: Abstract interface for catalog lookups.
- `LocalCatalogProvider`: Concrete implementation querying the local database.
- `AmazonProvider`, `FlipkartProvider`, `IKEAProvider`, `SwiggyProvider`, `ZomatoProvider`, `OYOProvider`: Extensible adapter stubs for future affiliate / live API integrations.
