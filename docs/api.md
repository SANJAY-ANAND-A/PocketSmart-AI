# PocketSmart AI API Specification

## Base URL
`/api`

---

## 1. Authentication Endpoints

### `POST /api/auth/register`
Creates a new user profile with securely hashed credentials. Passwords are encrypted using bcrypt.

- **Status Code:** `201 Created`
- **Request Body (`application/json`):**
  ```json
  {
    "email": "student@pocketsmart.ai",
    "username": "demo_student",
    "password": "StudentPass2026",
    "full_name": "College Student"
  }
  ```
- **Response Body (`201 Created`):**
  ```json
  {
    "id": 1,
    "email": "student@pocketsmart.ai",
    "username": "demo_student",
    "full_name": "College Student",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2026-10-03T16:46:02"
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Duplicate email or duplicate username.
  - `422 Unprocessable Entity`: Invalid email format or password shorter than 6 characters.

---

### `POST /api/auth/login`
Authenticates user credentials and generates a signed JSON Web Token (JWT).

- **Status Code:** `200 OK`
- **Request Body (`application/json`):**
  ```json
  {
    "username_or_email": "demo_student",
    "password": "StudentPass2026"
  }
  ```
- **Response Body (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "student@pocketsmart.ai",
      "username": "demo_student",
      "full_name": "College Student",
      "is_active": true,
      "is_superuser": false,
      "created_at": "2026-10-03T16:46:02"
    }
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Incorrect username/email or invalid password.
  - `400 Bad Request`: Inactive account.

---

### `GET /api/auth/me`
Retrieves current authenticated user details from the decoded JWT token.

- **Headers:** `Authorization: Bearer <access_token>`
- **Status Code:** `200 OK`
- **Response Body (`200 OK`):**
  ```json
  {
    "id": 1,
    "email": "student@pocketsmart.ai",
    "username": "demo_student",
    "full_name": "College Student",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2026-10-03T16:46:02"
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Missing, invalid, expired, or tampered token.

---

## 2. Product Catalog Endpoints

### `GET /api/products`
Retrieves products and services from the local catalog with multi-factor database filtering and pagination.

- **Query Parameters:**
  - `module` (optional): Filter by module (`home`, `party`, `jewelry`).
  - `category` (optional): Filter by category slug or name (e.g., `bed`, `necklace`, `food`).
  - `vendor` (optional): Filter by vendor or platform name (e.g., `IKEA`, `Amazon`, `Swiggy`, `OYO`).
  - `min_price` (optional): Minimum price in ₹ INR.
  - `max_price` (optional): Maximum price in ₹ INR.
  - `search` (optional): Keyword search matching name, description, subcategory, tags, or style.
  - `style` (optional): Filter by style (e.g., `Modern`, `Minimalist`, `Scandinavian`, `Traditional`, `Bohemian`).
  - `limit` (optional, default `20`, max `100`): Number of items per page.
  - `offset` (optional, default `0`): Pagination offset.
- **Status Code:** `200 OK`
- **Response Body:**
  ```json
  {
    "items": [
      {
        "id": 1,
        "name": "[DEMO] IKEA Malm Queen Storage Bed",
        "description": "[Sample Catalog] Hydraulic under-bed storage frame in oak veneer. Clean Scandinavian aesthetic.",
        "price": 27990.0,
        "currency": "INR",
        "currency_symbol": "₹",
        "category_id": 1,
        "category_name": "Bed",
        "module_type": "home",
        "subcategory": "Storage Bed",
        "platform": "IKEA",
        "vendor_id": 1,
        "vendor_name": "IKEA India",
        "rating": 4.6,
        "image_url": null,
        "product_url": null,
        "tags": "scandinavian,storage,wood,oak,queen-size",
        "style": "Scandinavian",
        "availability": true,
        "is_demo": true,
        "created_at": "2026-10-03T16:41:00"
      }
    ],
    "total": 33,
    "limit": 20,
    "offset": 0,
    "currency": "INR",
    "currency_symbol": "₹"
  }
  ```

---

### `GET /api/products/{id}`
Retrieves complete details for a single product or service item.

- **Parameters:** `id` (integer) - Product unique identifier.
- **Status Code:** `200 OK`
- **Response Body (`200 OK`):**
  ```json
  {
    "id": 1,
    "name": "[DEMO] IKEA Malm Queen Storage Bed",
    "description": "[Sample Catalog] Hydraulic under-bed storage frame in oak veneer.",
    "price": 27990.0,
    "currency": "INR",
    "currency_symbol": "₹",
    "category_id": 1,
    "category_name": "Bed",
    "module_type": "home",
    "subcategory": "Storage Bed",
    "platform": "IKEA",
    "vendor_id": 1,
    "vendor_name": "IKEA India",
    "rating": 4.6,
    "image_url": null,
    "product_url": null,
    "tags": "scandinavian,storage,wood,oak,queen-size",
    "style": "Scandinavian",
    "availability": true,
    "is_demo": true,
    "created_at": "2026-10-03T16:41:00"
  }
  ```
- **Error Responses:**
  - `404 Not Found`:
    ```json
    {
      "detail": "Product with ID 999999 was not found in the catalog."
    }
    ```

---

### `GET /api/products/categories`
Lists categories for populating dropdowns and filters.

- **Query Parameters:** `module` (optional, e.g. `home`, `party`, `jewelry`).
- **Status Code:** `200 OK`
- **Response Body:**
  ```json
  [
    {
      "id": 1,
      "name": "Bed",
      "slug": "bed",
      "module_type": "home",
      "description": "King, Queen, and single beds with storage options",
      "icon": "Bed"
    }
  ]
  ```

---

### `GET /api/products/vendors`
Lists registered vendors and platform providers.

- **Query Parameters:** `platform` (optional, e.g. `IKEA`, `Amazon`, `Swiggy`).
- **Status Code:** `200 OK`
- **Response Body:**
  ```json
  [
    {
      "id": 1,
      "name": "IKEA India",
      "platform": "IKEA",
      "description": "[DEMO DATA] Swedish home furnishings...",
      "rating": 4.6,
      "website_url": "https://www.ikea.com/in/en/",
      "is_demo": true
    }
  ]
  ```

---

## 3. Budget Planner Engine

### `POST /api/planner/budget`
Calculates item subtotals, total planned cost, remaining balance, over-budget deficits, and utilization percentage deterministically using `Decimal` arithmetic.

> **Security & Correctness Note:** Product prices are NEVER trusted from the frontend. The backend queries authoritative prices directly from SQLite catalog and multiplies by validated positive integer quantities.

- **Headers:** `Authorization: Bearer <access_token>` (Required)
- **Status Code:** `200 OK`
- **Request Body (`application/json`):**
  ```json
  {
    "module": "home",
    "total_budget": 50000.0,
    "items": [
      {
        "product_id": 1,
        "quantity": 1
      },
      {
        "product_id": 9,
        "quantity": 2
      }
    ],
    "title": "Master Bedroom Interior Setup",
    "save_plan": true
  }
  ```
- **Response Body (`200 OK`):**
  ```json
  {
    "module": "home",
    "total_budget": 50000.0,
    "total_cost": 37970.0,
    "remaining_budget": 12030.0,
    "over_budget_amount": 0.0,
    "utilization_percentage": 75.94,
    "is_within_budget": true,
    "currency": "INR",
    "currency_symbol": "₹",
    "items": [
      {
        "product_id": 1,
        "name": "[DEMO] IKEA Malm Queen Storage Bed",
        "unit_price": 27990.0,
        "quantity": 1,
        "subtotal": 27990.0,
        "category_name": "Bed",
        "module_type": "home",
        "platform": "IKEA",
        "is_demo": true
      },
      {
        "product_id": 9,
        "name": "[DEMO] IKEA Linnmon Ergonomic Work Desk",
        "unit_price": 4990.0,
        "quantity": 2,
        "subtotal": 9980.0,
        "category_name": "Table",
        "module_type": "home",
        "platform": "IKEA",
        "is_demo": true
      }
    ],
    "plan_id": 1,
    "title": "Master Bedroom Interior Setup"
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Module mismatch (e.g. including a jewelry ring inside a home planner).
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `404 Not Found`: One or more product IDs do not exist in the catalog.
  - `422 Unprocessable Entity`: Budget <= 0, quantity <= 0, empty item list, or invalid module.

---

## 4. AI-Powered Recommendations & Fallback

### `POST /api/recommendations`
Generates personalized catalog recommendations and budget plans. Combines Google Gemini GenAI for preference understanding with the deterministic Budget Engine for authoritative financial arithmetic. Seamlessly falls back to rule-based catalog matching if Gemini is unavailable or rate-limited.

- **Headers:** `Authorization: Bearer <access_token>` (Required)
- **Status Code:** `200 OK`
- **Request Body (`application/json`):**
  ```json
  {
    "module": "home",
    "budget": 50000.0,
    "preferences": "I want a modern minimalist bedroom with neutral colors and a queen bed.",
    "save_plan": true,
    "title": "Minimalist Bedroom Plan"
  }
  ```
- **Response Body (`200 OK`):**
  ```json
  {
    "source": "gemini",
    "module": "home",
    "summary": "Tailored minimalist bedroom setup prioritizing essential storage and restful sleep.",
    "budget_guidance": "Allocate majority of your budget to a sturdy storage bed frame.",
    "recommendations": [
      {
        "product": {
          "id": 1,
          "name": "[DEMO] IKEA Malm Queen Storage Bed",
          "description": "[Sample Catalog] Hydraulic under-bed storage frame in oak veneer.",
          "price": 27990.0,
          "currency": "INR",
          "currency_symbol": "₹",
          "category_id": 1,
          "category_name": "Bed",
          "module_type": "home",
          "subcategory": "Storage Bed",
          "platform": "IKEA",
          "vendor_name": "IKEA India",
          "rating": 4.6,
          "is_demo": true
        },
        "quantity": 1,
        "subtotal": 27990.0,
        "reason": "Fits the modern minimalist requirement with clean lines and functional under-bed storage."
      },
      {
        "product": {
          "id": 9,
          "name": "[DEMO] IKEA Linnmon Ergonomic Work Desk",
          "description": "[Sample Catalog] Minimalist white work desk with powder-coated legs.",
          "price": 4990.0,
          "currency": "INR",
          "currency_symbol": "₹",
          "category_id": 4,
          "category_name": "Table",
          "module_type": "home",
          "subcategory": "Study Desk",
          "platform": "IKEA",
          "vendor_name": "IKEA India",
          "rating": 4.5,
          "is_demo": true
        },
        "quantity": 1,
        "subtotal": 4990.0,
        "reason": "Compact study desk that blends seamlessly into the bedroom space."
      }
    ],
    "budget": {
      "total_budget": 50000.0,
      "total_cost": 32980.0,
      "remaining_budget": 17020.0,
      "is_within_budget": true,
      "over_budget_amount": 0.0,
      "utilization_percentage": 65.96,
      "currency": "INR",
      "currency_symbol": "₹"
    },
    "warnings": [],
    "plan_id": 2,
    "created_at": "2026-10-03T17:01:30"
  }
  ```
- **Fallback Response (`source: "deterministic_fallback"`):**
  When Gemini is unavailable or unconfigured, the system returns a rule-based plan with:
  ```json
  {
    "source": "deterministic_fallback",
    "warnings": [
      "AI recommendations are temporarily unavailable. Showing rule-based recommendations."
    ]
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `422 Unprocessable Entity`: Invalid module, negative budget, or empty preferences.

---

## 5. Home Interior Budget Planner

### `POST /api/planner/home`
Generates a complete room-by-room home interior budget plan. Enforces home-only catalog filtering, leverages Google Gemini AI for aesthetic matching (style, color palettes, furniture priorities), calculates accurate budget numbers with the deterministic Budget Engine, and saves the resulting plan for the user in SQLite.

- **Headers:** `Authorization: Bearer <access_token>` (Required)
- **Status Code:** `200 OK`
- **Supported Room Types:** `bedroom`, `living_room`, `dining_room`, `home_office`, `kitchen`, `studio`, `balcony`.
- **Request Body (`application/json`):**
  ```json
  {
    "budget": 80000.0,
    "room_type": "bedroom",
    "style": "Scandinavian",
    "color_preferences": ["white", "beige", "oak"],
    "priorities": ["bed", "wardrobe", "desk"],
    "required_items": ["queen storage bed", "wardrobe"],
    "preferences": "A peaceful Scandinavian master bedroom with oak wood accents and hidden storage.",
    "title": "Master Scandinavian Bedroom"
  }
  ```
- **Response Body (`200 OK`):**
  ```json
  {
    "module": "home",
    "source": "gemini",
    "plan": {
      "room_type": "bedroom",
      "style": "Scandinavian",
      "colors": ["white", "beige", "oak"],
      "priorities": ["bed", "wardrobe", "desk"],
      "required_items": ["queen storage bed", "wardrobe"]
    },
    "summary": "A serene Scandinavian bedroom layout prioritizing durable storage furniture and warm natural tones.",
    "budget_guidance": "Dedicate the primary budget share to the modular storage bed and wardrobe.",
    "recommendations": [
      {
        "product": {
          "id": 1,
          "name": "[DEMO] IKEA Malm Queen Storage Bed",
          "description": "[Sample Catalog] Hydraulic under-bed storage frame in oak veneer.",
          "price": 27990.0,
          "currency": "INR",
          "currency_symbol": "₹",
          "category_id": 1,
          "category_name": "Bed",
          "module_type": "home",
          "subcategory": "Storage Bed",
          "platform": "IKEA",
          "vendor_name": "IKEA India",
          "rating": 4.6,
          "is_demo": true
        },
        "quantity": 1,
        "subtotal": 27990.0,
        "reason": "Provides essential Scandinavian styling and hydraulic under-bed storage."
      },
      {
        "product": {
          "id": 7,
          "name": "[DEMO] IKEA Pax Modular 3-Door Wardrobe",
          "description": "[Sample Catalog] Spacious white modular wardrobe with soft-closing hinges.",
          "price": 28500.0,
          "currency": "INR",
          "currency_symbol": "₹",
          "category_id": 3,
          "category_name": "Wardrobe",
          "module_type": "home",
          "subcategory": "3-Door Wardrobe",
          "platform": "IKEA",
          "vendor_name": "IKEA India",
          "rating": 4.8,
          "is_demo": true
        },
        "quantity": 1,
        "subtotal": 28500.0,
        "reason": "High-capacity modular storage matching the room aesthetic."
      }
    ],
    "budget": {
      "total_budget": 80000.0,
      "total_cost": 56490.0,
      "remaining_budget": 23510.0,
      "is_within_budget": true,
      "over_budget_amount": 0.0,
      "utilization_percentage": 70.61,
      "currency": "INR",
      "currency_symbol": "₹"
    },
    "warnings": [],
    "plan_id": 3,
    "created_at": "2026-10-03T17:07:40"
  }
  ```
- **Fallback Response (`source: "deterministic_fallback"`):**
  When Gemini is unavailable, the response returns deterministic recommendations and appends:
  `"AI recommendations are temporarily unavailable. Showing rule-based recommendations."`
- **Error Responses:**
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `422 Unprocessable Entity`: Budget <= 0 or invalid `room_type` not in allowed room list.

---

## 6. Party / Event Budget Planner

### `POST /api/planner/party`
Generates a complete celebration and event budget plan based on event type, venue, guest count, food, and entertainment preferences. Enforces party-only catalog filtering (Amazon, Swiggy, Zomato, OYO, Local), computes deterministic category budget allocations, performs guest-count scaling, applies Google Gemini AI for contextual curation, enforces budget invariants with the deterministic Budget Engine, and persists the resulting plan for the user in SQLite.

- **Headers:** `Authorization: Bearer <access_token>` (Required)
- **Status Code:** `200 OK`
- **Supported Event Types:** `birthday`, `wedding`, `corporate_event`, `college_event`, `anniversary`, `small_gathering`.
- **Supported Venue Types:** `banquet_hall`, `hotel`, `outdoor`, `restaurant`, `community_hall`, `home`, `college_campus`, `other`.
- **Request Body (`application/json`):**
  ```json
  {
    "budget": 120000.0,
    "guest_count": 60,
    "event_type": "birthday",
    "venue_type": "banquet_hall",
    "food_preference": "vegetarian",
    "decoration_preference": "balloon",
    "entertainment_preference": "dj",
    "event_duration_hours": 4.0,
    "preferences": "A fun 60-guest celebration with lively music and balloon arch decor.",
    "title": "Grand 60th Celebration"
  }
  ```
- **Response Body (`200 OK`):**
  ```json
  {
    "module": "party",
    "source": "gemini",
    "plan_id": 4,
    "plan": {
      "event_type": "birthday",
      "guest_count": 60,
      "venue_type": "banquet_hall",
      "food_preference": "vegetarian",
      "decoration_preference": "balloon",
      "entertainment_preference": "dj",
      "event_duration_hours": 4.0,
      "estimated_food_budget_per_guest": 680.0
    },
    "category_allocations": [
      {"category": "food", "allocated_amount": 40800.0, "percentage": 34.0},
      {"category": "venue", "allocated_amount": 33600.0, "percentage": 28.0},
      {"category": "decoration", "allocated_amount": 14400.0, "percentage": 12.0},
      {"category": "entertainment", "allocated_amount": 12000.0, "percentage": 10.0},
      {"category": "photography", "allocated_amount": 12000.0, "percentage": 10.0},
      {"category": "transportation", "allocated_amount": 2400.0, "percentage": 2.0},
      {"category": "miscellaneous", "allocated_amount": 4800.0, "percentage": 4.0}
    ],
    "summary": "Tailored celebration plan featuring banquet venue, bulk buffet catering, balloon arch, and sound rig.",
    "budget_guidance": "Prioritize venue and bulk catering contracts before finalizing decor and DJ.",
    "recommendations": [
      {
        "product": {
          "id": 16,
          "name": "[DEMO] Grand Heritage Banquet Lawn Space",
          "description": "[Sample Catalog] Open garden venue with banquet hall.",
          "price": 48000.0,
          "currency": "INR",
          "currency_symbol": "₹",
          "category_id": 11,
          "category_name": "Venue",
          "module_type": "party",
          "subcategory": "Banquet Lawn",
          "platform": "Local",
          "vendor_name": "Local Heritage Crafts & Studio",
          "rating": 4.7,
          "is_demo": true
        },
        "quantity": 1,
        "subtotal": 48000.0,
        "reason": "Banquet lawn space accommodating 60 attendees with ample staging area."
      },
      {
        "product": {
          "id": 14,
          "name": "[DEMO] Swiggy Premium Buffet Catering (50 Guests)",
          "description": "[Sample Catalog] 3-course multi-cuisine buffet package.",
          "price": 28000.0,
          "currency": "INR",
          "currency_symbol": "₹",
          "category_id": 10,
          "category_name": "Food",
          "module_type": "party",
          "subcategory": "Buffet Catering",
          "platform": "Swiggy",
          "vendor_name": "Swiggy Gourmet & Bulk Events",
          "rating": 4.6,
          "is_demo": true
        },
        "quantity": 2,
        "subtotal": 56000.0,
        "reason": "2 catering packages scaled to serve up to 100 attendees for 60 guests."
      }
    ],
    "budget": {
      "total_budget": 120000.0,
      "total_cost": 104000.0,
      "remaining_budget": 16000.0,
      "is_within_budget": true,
      "over_budget_amount": 0.0,
      "utilization_percentage": 86.67,
      "currency": "INR",
      "currency_symbol": "₹"
    },
    "warnings": [],
    "created_at": "2026-10-03T17:15:00"
  }
  ```
- **Fallback Response (`source: "deterministic_fallback"`):**
  When Gemini is unavailable, returns a rule-based plan selecting core party components within budget and appends:
  `"AI recommendations are temporarily unavailable. Showing rule-based recommendations."`
- **Error Responses:**
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `422 Unprocessable Entity`: Budget <= 0, guest_count <= 0 or > 10,000, duration < 1 or > 72 hours, or unsupported event/venue types.

---

## 7. Jewelry Budget Planner

### `POST /api/planner/jewelry`
Generates a complete jewelry ensemble budget plan based on occasion, style, metal, and stone/color preferences. Supports an optional outfit image for multimodal Gemini AI visual styling analysis with strict privacy guardrails (no face/identity recognition). Enforces jewelry-only catalog filtering (Amazon, Flipkart, Local), computes deterministic category budget allocations, applies Budget Engine arithmetic guarantees, and persists the resulting plan in SQLite.

- **Headers:** `Authorization: Bearer <access_token>` (Required)
- **Supported Encodings:**
  - `application/json` (pure JSON payload without image)
  - `multipart/form-data` or `application/x-www-form-urlencoded` (with optional `outfit_image` file upload)
- **Supported Occasions:** `wedding`, `engagement`, `birthday`, `party`, `traditional_event`, `formal_event`.
- **Supported Jewelry Types:** `necklace`, `earrings`, `bracelet`, `ring`, `pendant`, `bangles`, `complete_set`, `any`.
- **Supported Metals:** `gold`, `rose_gold`, `silver`, `platinum`, `brass`, `oxidized_silver`, `any`.
- **Image Requirements (Optional):**
  - Formats: JPEG, PNG, WEBP.
  - Maximum size: 5 MB.
  - Processing lifecycle: validated, decoded in memory, evaluated by Gemini backend-only, and discarded immediately. No public exposure or permanent storage.
  - Privacy constraint: AI analysis is restricted exclusively to fabric, dominant colors, neckline, and styling formality. No face, identity, or biometric recognition is performed.
- **Request Body (JSON Example):**
  ```json
  {
    "budget": 75000.0,
    "occasion": "wedding",
    "style": "Traditional",
    "preferred_metal": "gold",
    "preferred_color": "ruby-red",
    "jewelry_type": "necklace",
    "preferences": "Bridal traditional jewelry set with pearl accents and matching earrings.",
    "title": "Bridal Traditional Gold Set"
  }
  ```
- **Multipart Form Example:**
  - Form fields: `budget=75000`, `occasion=wedding`, `style=Traditional`, `preferred_metal=gold`
  - File field: `outfit_image=@my_saree.jpg;type=image/jpeg`
- **Response Body (`200 OK`):**
  ```json
  {
    "module": "jewelry",
    "source": "gemini",
    "plan_id": 5,
    "plan": {
      "occasion": "wedding",
      "style": "Traditional",
      "preferred_metal": "gold",
      "preferred_color": "ruby-red",
      "jewelry_type": "necklace",
      "outfit_analyzed": true
    },
    "category_allocations": [
      {"category": "necklace", "allocated_amount": 45000.0, "percentage": 60.0},
      {"category": "earrings", "allocated_amount": 15000.0, "percentage": 20.0},
      {"category": "ring", "allocated_amount": 7500.0, "percentage": 10.0},
      {"category": "bracelet", "allocated_amount": 3750.0, "percentage": 5.0},
      {"category": "bangles", "allocated_amount": 3750.0, "percentage": 5.0}
    ],
    "summary": "Bridal gold ensemble harmonized with traditional red accents and intricate filigree work.",
    "budget_guidance": "Prioritize the central Kundan choker before adding accent rings.",
    "recommendations": [
      {
        "product": {
          "id": 25,
          "name": "[DEMO] Royal Kundan & Pearl Bridal Choker Set",
          "description": "[Sample Catalog] 22K gold-plated handcrafted Kundan choker necklace.",
          "price": 32999.0,
          "currency": "INR",
          "currency_symbol": "₹",
          "category_id": 17,
          "category_name": "Necklace",
          "module_type": "jewelry",
          "subcategory": "Choker Set",
          "platform": "Local",
          "vendor_name": "Local Heritage Crafts & Studio",
          "rating": 4.9,
          "is_demo": true
        },
        "quantity": 1,
        "subtotal": 32999.0,
        "reason": "Centerpiece 22K gold-plated Kundan choker with pearls matching bridal requirements."
      },
      {
        "product": {
          "id": 27,
          "name": "[DEMO] Handcrafted Meenakari Chandbali Earrings",
          "description": "[Sample Catalog] Traditional Rajasthani enamelled peacock chandbali earrings.",
          "price": 2899.0,
          "currency": "INR",
          "currency_symbol": "₹",
          "category_id": 18,
          "category_name": "Earrings",
          "module_type": "jewelry",
          "subcategory": "Chandbali",
          "platform": "Flipkart",
          "vendor_name": "Flipkart Retail",
          "rating": 4.5,
          "is_demo": true
        },
        "quantity": 1,
        "subtotal": 2899.0,
        "reason": "Intricate peacock Meenakari chandbalis that complement the choker necklace."
      }
    ],
    "budget": {
      "total_budget": 75000.0,
      "total_cost": 35898.0,
      "remaining_budget": 39102.0,
      "is_within_budget": true,
      "over_budget_amount": 0.0,
      "utilization_percentage": 47.86,
      "currency": "INR",
      "currency_symbol": "₹"
    },
    "warnings": [],
    "created_at": "2026-10-03T17:28:00"
  }
  ```
- **Fallback Response (`source: "deterministic_fallback"`):**
  When Gemini is unavailable, returns a rule-based plan selecting core jewelry items matching user preferences within budget and appends:
  `"AI recommendations are temporarily unavailable. Showing rule-based recommendations."`
- **Error Responses:**
  - `400 Bad Request`: Corrupt image, unsupported image MIME type.
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `413 Request Entity Too Large`: Image file exceeds 5 MB.
  - `422 Unprocessable Entity`: Budget <= 0, invalid occasion, or invalid jewelry type.

---

## 8. Saved Plans & Budget History Endpoints

All saved plan endpoints require JWT Bearer authentication (`Authorization: Bearer <access_token>`). Strict ownership isolation is enforced across all operations: queries are strictly filtered by the authenticated user's ID (`current_user.id`), and any attempt to view or delete another user's plan returns `404 Not Found` to prevent data leakage and enumeration attacks.

---

### `GET /api/plans`
Retrieves a summary list of saved budget plans belonging exclusively to the authenticated user.

- **Headers:** `Authorization: Bearer <access_token>`
- **Query Parameters:**
  - `module` (optional): Filter plans by planner module type. Valid values: `home`, `party`, `jewelry`. Providing an invalid value returns `422 Unprocessable Entity`.
- **Status Code:** `200 OK`
- **Response Body (`200 OK`):**
  ```json
  {
    "items": [
      {
        "id": 14,
        "title": "Minimalist Bedroom Renovation",
        "module_type": "home",
        "total_budget": 100000.0,
        "allocated_budget": 85990.0,
        "remaining_budget": 14010.0,
        "currency": "INR",
        "currency_symbol": "₹",
        "is_fallback": false,
        "items_count": 3,
        "recommendations_count": 3,
        "created_at": "2026-10-03T16:50:00",
        "updated_at": "2026-10-03T16:50:00"
      },
      {
        "id": 15,
        "title": "21st Birthday Bash",
        "module_type": "party",
        "total_budget": 50000.0,
        "allocated_budget": 46500.0,
        "remaining_budget": 3500.0,
        "currency": "INR",
        "currency_symbol": "₹",
        "is_fallback": false,
        "items_count": 4,
        "recommendations_count": 4,
        "created_at": "2026-10-03T17:10:00",
        "updated_at": "2026-10-03T17:10:00"
      }
    ],
    "total": 2
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `422 Unprocessable Entity`: Invalid module filter parameter (must be `home`, `party`, or `jewelry`).

---

### `GET /api/plans/{plan_id}`
Retrieves the complete details of a specific saved plan, including budget item allocations, product recommendations, catalog details, and AI reasoning notes.

- **Headers:** `Authorization: Bearer <access_token>`
- **Path Parameters:**
  - `plan_id` (integer, required): ID of the saved plan.
- **Status Code:** `200 OK`
- **Response Body (`200 OK`):**
  ```json
  {
    "id": 14,
    "title": "Minimalist Bedroom Renovation",
    "module_type": "home",
    "total_budget": 100000.0,
    "allocated_budget": 85990.0,
    "remaining_budget": 14010.0,
    "currency": "INR",
    "currency_symbol": "₹",
    "is_fallback": false,
    "preferences": {
      "room_type": "bedroom",
      "style": "Modern Minimalist",
      "primary_color": "neutral"
    },
    "ai_reasoning": "Plan prioritizes high-durability storage bed and functional workspace while staying within allocated budget.",
    "items": [
      {
        "id": 41,
        "category_name": "Bed",
        "allocated_amount": 50000.0,
        "spent_amount": 27990.0,
        "priority": "high",
        "reason": "Central bedroom furniture piece",
        "created_at": "2026-10-03T16:50:00"
      }
    ],
    "recommendations": [
      {
        "id": 82,
        "product_id": 1,
        "match_score": 0.95,
        "recommendation_reason": "Hydraulic storage bed offering clean minimalist look with maximum utility.",
        "is_upgrade": false,
        "product": {
          "id": 1,
          "name": "[DEMO] IKEA Malm Queen Storage Bed",
          "description": "[Sample Catalog] Hydraulic under-bed storage frame in oak veneer.",
          "price": 27990.0,
          "currency": "INR",
          "currency_symbol": "₹",
          "category_id": 1,
          "category_name": "Bed",
          "module_type": "home",
          "subcategory": "Storage Bed",
          "platform": "IKEA",
          "vendor_name": "IKEA India",
          "rating": 4.6,
          "is_demo": true
        }
      }
    ],
    "created_at": "2026-10-03T16:50:00",
    "updated_at": "2026-10-03T16:50:00"
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `404 Not Found`: Plan does not exist or belongs to another user (strictly prevents unauthorized access).

---

### `DELETE /api/plans/{plan_id}`
Deletes a saved budget plan belonging to the authenticated user. All associated `BudgetItem` and `Recommendation` child records are automatically deleted via SQLAlchemy cascade delete (`cascade="all, delete-orphan"`).

- **Headers:** `Authorization: Bearer <access_token>`
- **Path Parameters:**
  - `plan_id` (integer, required): ID of the plan to delete.
- **Status Code:** `200 OK`
- **Response Body (`200 OK`):**
  ```json
  {
    "detail": "Budget plan deleted successfully.",
    "plan_id": 14
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `404 Not Found`: Plan does not exist or belongs to another user (cannot delete another user's plan).

---

## 9. Health & System Endpoints

### `GET /api/health`
System health check returning database and API status.

- **Status Code:** `200 OK`
- **Response Body (`200 OK`):**
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "environment": "development",
    "database": "connected"
  }
  ```
