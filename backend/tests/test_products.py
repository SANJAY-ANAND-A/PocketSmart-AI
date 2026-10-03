import pytest
from fastapi.testclient import TestClient
from app.core.database import SessionLocal, init_db
from app.main import app
from app.models.product import Product
from app.seed import seed_database

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_catalog():
    init_db()
    seed_database()


def test_get_products_list_default():
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 30
    assert len(data["items"]) <= 20
    assert data["currency"] == "INR"
    assert data["currency_symbol"] == "₹"


def test_get_products_module_filtering():
    # 1. Home Module
    res_home = client.get("/api/products?module=home")
    assert res_home.status_code == 200
    home_items = res_home.json()["items"]
    assert len(home_items) > 0
    for item in home_items:
        assert item["module_type"] == "home"

    # 2. Party Module
    res_party = client.get("/api/products?module=party")
    assert res_party.status_code == 200
    party_items = res_party.json()["items"]
    assert len(party_items) > 0
    for item in party_items:
        assert item["module_type"] == "party"

    # 3. Jewelry Module
    res_jewelry = client.get("/api/products?module=jewelry")
    assert res_jewelry.status_code == 200
    jewelry_items = res_jewelry.json()["items"]
    assert len(jewelry_items) > 0
    for item in jewelry_items:
        assert item["module_type"] == "jewelry"


def test_get_products_category_filtering():
    # Category = Bed
    response = client.get("/api/products?category=Bed")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 0
    for item in items:
        assert "bed" in item["category_name"].lower() or "bed" in (item["subcategory"] or "").lower()


def test_get_products_vendor_filtering():
    # Vendor = IKEA
    response = client.get("/api/products?vendor=IKEA")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 0
    for item in items:
        assert "ikea" in item["platform"].lower() or "ikea" in (item["vendor_name"] or "").lower()

    # Vendor = Swiggy
    res_swiggy = client.get("/api/products?vendor=Swiggy")
    assert res_swiggy.status_code == 200
    swiggy_items = res_swiggy.json()["items"]
    assert len(swiggy_items) > 0
    for item in swiggy_items:
        assert "swiggy" in item["platform"].lower() or "swiggy" in (item["vendor_name"] or "").lower()


def test_get_products_price_filtering():
    # Min price = 15000
    res_min = client.get("/api/products?min_price=15000")
    assert res_min.status_code == 200
    items_min = res_min.json()["items"]
    assert len(items_min) > 0
    for item in items_min:
        assert item["price"] >= 15000

    # Max price = 5000
    res_max = client.get("/api/products?max_price=5000")
    assert res_max.status_code == 200
    items_max = res_max.json()["items"]
    assert len(items_max) > 0
    for item in items_max:
        assert item["price"] <= 5000


def test_get_products_search_filtering():
    response = client.get("/api/products?search=sofa")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 0
    for item in items:
        searchable_text = f"{item['name']} {item['description']} {item['tags']} {item['subcategory']}".lower()
        assert "sofa" in searchable_text


def test_get_products_combined_filters():
    # Module=home, Vendor=IKEA, max_price=35000
    response = client.get("/api/products?module=home&vendor=IKEA&max_price=35000")
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    assert len(items) > 0
    for item in items:
        assert item["module_type"] == "home"
        assert "ikea" in item["platform"].lower()
        assert item["price"] <= 35000


def test_get_products_pagination():
    res_p1 = client.get("/api/products?limit=5&offset=0")
    res_p2 = client.get("/api/products?limit=5&offset=5")

    assert res_p1.status_code == 200
    assert res_p2.status_code == 200

    d1 = res_p1.json()
    d2 = res_p2.json()

    assert len(d1["items"]) == 5
    assert len(d2["items"]) == 5
    assert d1["limit"] == 5
    assert d1["offset"] == 0
    assert d2["offset"] == 5

    # Verify no overlap between page 1 and page 2 IDs
    p1_ids = [item["id"] for item in d1["items"]]
    p2_ids = [item["id"] for item in d2["items"]]
    assert set(p1_ids).isdisjoint(set(p2_ids))


def test_get_product_by_id_valid():
    # Fetch first product to get its ID
    db = SessionLocal()
    first_prod = db.query(Product).first()
    db.close()
    assert first_prod is not None

    response = client.get(f"/api/products/{first_prod.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == first_prod.id
    assert data["name"] == first_prod.name
    assert data["price"] == first_prod.price
    assert data["currency"] == "INR"
    assert data["currency_symbol"] == "₹"
    assert data["is_demo"] is True


def test_get_product_by_id_not_found():
    response = client.get("/api/products/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_categories_endpoint():
    # 1. All categories
    response = client.get("/api/products/categories")
    assert response.status_code == 200
    cats = response.json()
    assert len(cats) >= 22

    # 2. Filtered by module=jewelry
    res_j = client.get("/api/products/categories?module=jewelry")
    assert res_j.status_code == 200
    jewelry_cats = res_j.json()
    assert len(jewelry_cats) == 6
    for c in jewelry_cats:
        assert c["module_type"] == "jewelry"


def test_get_vendors_endpoint():
    # 1. All vendors
    response = client.get("/api/products/vendors")
    assert response.status_code == 200
    vendors = response.json()
    assert len(vendors) >= 7

    platforms = {v["platform"] for v in vendors}
    assert {"IKEA", "Amazon", "Flipkart", "Swiggy", "Zomato", "OYO", "Local"}.issubset(platforms)
    for v in vendors:
        assert v["is_demo"] is True

    # 2. Filtered by platform=OYO
    res_oyo = client.get("/api/products/vendors?platform=OYO")
    assert res_oyo.status_code == 200
    oyo_vendors = res_oyo.json()
    assert len(oyo_vendors) == 1
    assert oyo_vendors[0]["platform"] == "OYO"


def test_product_schema_demo_flags_and_details():
    response = client.get("/api/products?limit=10")
    assert response.status_code == 200
    items = response.json()["items"]
    for item in items:
        assert "id" in item
        assert "name" in item
        assert "price" in item
        assert "currency" in item
        assert "currency_symbol" in item
        assert "category_id" in item
        assert "category_name" in item
        assert "module_type" in item
        assert "platform" in item
        assert "rating" in item
        assert "is_demo" in item
        assert item["is_demo"] is True
