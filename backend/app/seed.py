import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.models.category import Category
from app.models.product import Product
from app.models.vendor import Vendor

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Sample Vendors covering the required platforms
VENDORS_DATA = [
    {
        "name": "IKEA India",
        "platform": "IKEA",
        "description": "[DEMO DATA] Swedish home furnishings, flat-pack furniture, and modular storage solutions.",
        "contact_email": "demo.support@ikea.sample.in",
        "rating": 4.6,
        "website_url": "https://www.ikea.com/in/en/",
        "is_demo": True,
    },
    {
        "name": "Amazon India Home & Lifestyle",
        "platform": "Amazon",
        "description": "[DEMO DATA] Online marketplace offering furniture, lighting, jewelry, and party decor.",
        "contact_email": "demo.seller@amazon.sample.in",
        "rating": 4.4,
        "website_url": "https://www.amazon.in",
        "is_demo": True,
    },
    {
        "name": "Flipkart Retail",
        "platform": "Flipkart",
        "description": "[DEMO DATA] E-commerce platform featuring home furnishings, electronics, and accessories.",
        "contact_email": "demo.support@flipkart.sample.in",
        "rating": 4.3,
        "website_url": "https://www.flipkart.com",
        "is_demo": True,
    },
    {
        "name": "Swiggy Gourmet & Bulk Events",
        "platform": "Swiggy",
        "description": "[DEMO DATA] Food delivery and party catering service for gatherings and celebrations.",
        "contact_email": "demo.events@swiggy.sample.in",
        "rating": 4.5,
        "website_url": "https://www.swiggy.com",
        "is_demo": True,
    },
    {
        "name": "Zomato Catering Solutions",
        "platform": "Zomato",
        "description": "[DEMO DATA] Party snack boxes, gourmet platters, and full buffet meal catering partners.",
        "contact_email": "demo.catering@zomato.sample.in",
        "rating": 4.5,
        "website_url": "https://www.zomato.com",
        "is_demo": True,
    },
    {
        "name": "OYO Townhouse & Celebration Spaces",
        "platform": "OYO",
        "description": "[DEMO DATA] Boutique event spaces, banquet halls, and terrace venues for parties.",
        "contact_email": "demo.venues@oyo.sample.in",
        "rating": 4.2,
        "website_url": "https://www.oyorooms.com",
        "is_demo": True,
    },
    {
        "name": "Local Heritage Crafts & Studio",
        "platform": "Local",
        "description": "[DEMO DATA] Independent artisans, custom jewelers, local photographers, and decorators.",
        "contact_email": "demo.artisan@local.sample.in",
        "rating": 4.7,
        "website_url": "https://local-artisan.sample",
        "is_demo": True,
    },
]

# Taxonomy Categories
CATEGORIES_DATA = [
    # Home Interior
    {"name": "Bed", "slug": "bed", "module_type": "home", "description": "King, Queen, and single beds with storage options", "icon": "Bed"},
    {"name": "Sofa", "slug": "sofa", "module_type": "home", "description": "Sectional sofas, 3-seater couches, and recliners", "icon": "Sofa"},
    {"name": "Wardrobe", "slug": "wardrobe", "module_type": "home", "description": "Sliding and modular wardrobe closets", "icon": "Archive"},
    {"name": "Table", "slug": "table", "module_type": "home", "description": "Coffee tables, dining tables, and study desks", "icon": "Table"},
    {"name": "Chair", "slug": "chair", "module_type": "home", "description": "Ergonomic work chairs and dining chairs", "icon": "Armchair"},
    {"name": "Lighting", "slug": "lighting", "module_type": "home", "description": "Pendant lights, ceiling lamps, and ambient strips", "icon": "Lamp"},
    {"name": "Curtains", "slug": "curtains", "module_type": "home", "description": "Blackout drapes and sheer window curtains", "icon": "Blinds"},
    {"name": "Decor", "slug": "decor", "module_type": "home", "description": "Wall art, mirrors, vases, and indoor planters", "icon": "Palette"},
    {"name": "Storage", "slug": "storage", "module_type": "home", "description": "Bookshelves, TV units, and organizer cabinets", "icon": "Box"},

    # Party / Event
    {"name": "Food", "slug": "party-food", "module_type": "party", "description": "Catering, buffet meals, live food counters, and desserts", "icon": "Utensils"},
    {"name": "Venue", "slug": "party-venue", "module_type": "party", "description": "Banquet halls, rooftop party spaces, and private lawns", "icon": "Building"},
    {"name": "Decoration", "slug": "party-decoration", "module_type": "party", "description": "Floral backdrops, balloon arches, and thematic lighting", "icon": "Sparkles"},
    {"name": "Entertainment", "slug": "party-entertainment", "module_type": "party", "description": "Live DJ, sound systems, acoustic bands, and MCs", "icon": "Music"},
    {"name": "Photography", "slug": "party-photography", "module_type": "party", "description": "Candid photographers, cinematic video, and photo booths", "icon": "Camera"},
    {"name": "Transportation", "slug": "party-transportation", "module_type": "party", "description": "Guest shuttle minibuses, luxury car rentals", "icon": "Bus"},
    {"name": "Miscellaneous", "slug": "party-misc", "module_type": "party", "description": "Party favors, eco-friendly cutlery, signage, and props", "icon": "Package"},

    # Jewelry
    {"name": "Necklace", "slug": "jewelry-necklace", "module_type": "jewelry", "description": "Chokers, bridal kundan necklaces, and minimalist chains", "icon": "Gem"},
    {"name": "Earrings", "slug": "jewelry-earrings", "module_type": "jewelry", "description": "Jhumkas, diamond studs, and dangling chandbalis", "icon": "Disc"},
    {"name": "Bracelet", "slug": "jewelry-bracelet", "module_type": "jewelry", "description": "Charm bracelets, tennis bracelets, and silver cuffs", "icon": "Circle"},
    {"name": "Ring", "slug": "jewelry-ring", "module_type": "jewelry", "description": "Solitaire rings, cocktail rings, and gold bands", "icon": "Target"},
    {"name": "Pendant", "slug": "jewelry-pendant", "module_type": "jewelry", "description": "Gemstone pendants, pearl drops, and lockets", "icon": "Shield"},
    {"name": "Bangles", "slug": "jewelry-bangles", "module_type": "jewelry", "description": "Traditional gold-tone kadas and glass bangle sets", "icon": "Sun"},
]

# Realistic INR (₹) catalog items labeled as DEMO DATA
PRODUCTS_DATA = [
    # ------------------ HOME INTERIOR ------------------
    {
        "name": "[DEMO] IKEA Malm Queen Storage Bed",
        "description": "[Sample Catalog] Hydraulic under-bed storage frame in oak veneer. Clean Scandinavian aesthetic.",
        "category_slug": "bed",
        "subcategory": "Storage Bed",
        "platform": "IKEA",
        "vendor_name": "IKEA India",
        "price": 27990.0,
        "rating": 4.6,
        "style": "Scandinavian",
        "tags": "scandinavian,storage,wood,oak,queen-size",
    },
    {
        "name": "[DEMO] Solimo Solid Wood Queen Bed",
        "description": "[Sample Catalog] Teak-finish solid Sheesham wood bed with upholstered headboard.",
        "category_slug": "bed",
        "subcategory": "Solid Wood Bed",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 18499.0,
        "rating": 4.3,
        "style": "Modern",
        "tags": "modern,solid-wood,teak,queen-size,budget-friendly",
    },
    {
        "name": "[DEMO] UrbanFurn Engineered Wood King Bed",
        "description": "[Sample Catalog] Contemporary engineered wood bed with box storage and dark walnut finish.",
        "category_slug": "bed",
        "subcategory": "Box Storage Bed",
        "platform": "Flipkart",
        "vendor_name": "Flipkart Retail",
        "price": 14999.0,
        "rating": 4.1,
        "style": "Minimalist",
        "tags": "minimalist,engineered-wood,walnut,king-size,budget",
    },
    {
        "name": "[DEMO] IKEA Friheten Corner Sofa Bed",
        "description": "[Sample Catalog] Convertible 3-seat sofa bed with hidden storage chaise in dark grey fabric.",
        "category_slug": "sofa",
        "subcategory": "Sofa Bed",
        "platform": "IKEA",
        "vendor_name": "IKEA India",
        "price": 34990.0,
        "rating": 4.7,
        "style": "Modern",
        "tags": "modern,convertible,sofa-bed,fabric,grey,storage",
    },
    {
        "name": "[DEMO] CasaCraft 3-Seater Velvet Sofa",
        "description": "[Sample Catalog] Elegant jewel-toned royal blue velvet sofa with brass-tipped tapered legs.",
        "category_slug": "sofa",
        "subcategory": "3-Seater Sofa",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 22499.0,
        "rating": 4.4,
        "style": "Bohemian",
        "tags": "bohemian,velvet,blue,brass,luxury,living-room",
    },
    {
        "name": "[DEMO] Woodart 2-Door Wardrobe with Mirror",
        "description": "[Sample Catalog] Compact 2-door wardrobe with built-in dressing mirror and hanging rod.",
        "category_slug": "wardrobe",
        "subcategory": "2-Door Wardrobe",
        "platform": "Flipkart",
        "vendor_name": "Flipkart Retail",
        "price": 11499.0,
        "rating": 4.2,
        "style": "Minimalist",
        "tags": "minimalist,mirror,compact,bedroom,budget",
    },
    {
        "name": "[DEMO] IKEA Pax Modular 3-Door Wardrobe",
        "description": "[Sample Catalog] Spacious white modular wardrobe with soft-closing hinges and drawer organizers.",
        "category_slug": "wardrobe",
        "subcategory": "3-Door Wardrobe",
        "platform": "IKEA",
        "vendor_name": "IKEA India",
        "price": 28500.0,
        "rating": 4.8,
        "style": "Scandinavian",
        "tags": "scandinavian,modular,white,large,spacious,premium",
    },
    {
        "name": "[DEMO] Solid Teak 4-Seater Dining Table",
        "description": "[Sample Catalog] Handcrafted Sheesham wood dining table with natural matte grain polish.",
        "category_slug": "table",
        "subcategory": "Dining Table",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 12999.0,
        "rating": 4.5,
        "style": "Traditional",
        "tags": "traditional,dining,teak,solid-wood,family",
    },
    {
        "name": "[DEMO] IKEA Linnmon Ergonomic Work Desk",
        "description": "[Sample Catalog] Minimalist white work desk with cable grommet and steel powder-coated legs.",
        "category_slug": "table",
        "subcategory": "Study Desk",
        "platform": "IKEA",
        "vendor_name": "IKEA India",
        "price": 4990.0,
        "rating": 4.5,
        "style": "Minimalist",
        "tags": "minimalist,desk,study,office,compact",
    },
    {
        "name": "[DEMO] Green Soul High-Back Ergonomic Chair",
        "description": "[Sample Catalog] Breathable mesh high-back chair with lumbar adjustment and 2D armrests.",
        "category_slug": "chair",
        "subcategory": "Office Chair",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 6499.0,
        "rating": 4.6,
        "style": "Modern",
        "tags": "modern,ergonomic,mesh,office,study,work-from-home",
    },
    {
        "name": "[DEMO] Philips Hue Smart Ambient Pendant Lamp",
        "description": "[Sample Catalog] Warm brass geometric ceiling pendant light with dimmable warm-to-cool LED.",
        "category_slug": "lighting",
        "subcategory": "Pendant Light",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 3299.0,
        "rating": 4.4,
        "style": "Industrial",
        "tags": "industrial,brass,pendant,smart-lighting,ambient",
    },
    {
        "name": "[DEMO] UrbanSpace 100% Blackout Room Curtains",
        "description": "[Sample Catalog] Set of 2 thermal insulated linen-texture eyelet curtains (7ft, Charcoal Grey).",
        "category_slug": "curtains",
        "subcategory": "Blackout Curtains",
        "platform": "Flipkart",
        "vendor_name": "Flipkart Retail",
        "price": 1499.0,
        "rating": 4.3,
        "style": "Modern",
        "tags": "modern,curtains,blackout,grey,linen",
    },
    {
        "name": "[DEMO] Artisanal Brass Round Wall Mirror (24-inch)",
        "description": "[Sample Catalog] Handcrafted antique gold finish vanity wall accent mirror.",
        "category_slug": "decor",
        "subcategory": "Wall Mirror",
        "platform": "Local",
        "vendor_name": "Local Heritage Crafts & Studio",
        "price": 2899.0,
        "rating": 4.7,
        "style": "Traditional",
        "tags": "traditional,handcrafted,brass,mirror,wall-decor",
    },
    {
        "name": "[DEMO] IKEA Kallax 4-Shelf Storage Cube Unit",
        "description": "[Sample Catalog] Versatile cube shelving unit in white oak finish. Can be used vertical or horizontal.",
        "category_slug": "storage",
        "subcategory": "Shelving Unit",
        "platform": "IKEA",
        "vendor_name": "IKEA India",
        "price": 5490.0,
        "rating": 4.7,
        "style": "Scandinavian",
        "tags": "scandinavian,storage,cube,bookshelf,modular",
    },

    # ------------------ PARTY / EVENT ------------------
    {
        "name": "[DEMO] Swiggy Premium Buffet Catering (50 Guests)",
        "description": "[Sample Catalog] 3-course multi-cuisine buffet package including appetizers, mains, and desserts.",
        "category_slug": "party-food",
        "subcategory": "Buffet Catering",
        "platform": "Swiggy",
        "vendor_name": "Swiggy Gourmet & Bulk Events",
        "price": 28000.0,
        "rating": 4.6,
        "style": "Modern",
        "tags": "food,catering,buffet,50-guests,multicuisine,dinner",
    },
    {
        "name": "[DEMO] Zomato Live Street Snack & Chaat Station",
        "description": "[Sample Catalog] Live counter with Pani Puri, Sev Puri, Dim Sums, and Mocktails (25-40 guests).",
        "category_slug": "party-food",
        "subcategory": "Live Counter",
        "platform": "Zomato",
        "vendor_name": "Zomato Catering Solutions",
        "price": 14500.0,
        "rating": 4.5,
        "style": "Bohemian",
        "tags": "food,chaat,street-food,live-counter,snacks,cocktail-party",
    },
    {
        "name": "[DEMO] OYO Townhouse Rooftop Celebration Hall",
        "description": "[Sample Catalog] 1,500 sq.ft covered rooftop terrace with ambient fairy lights, sound system & AC lounge.",
        "category_slug": "party-venue",
        "subcategory": "Rooftop Venue",
        "platform": "OYO",
        "vendor_name": "OYO Townhouse & Celebration Spaces",
        "price": 24999.0,
        "rating": 4.3,
        "style": "Modern",
        "tags": "venue,rooftop,terrace,party-hall,oyo,air-conditioned",
    },
    {
        "name": "[DEMO] Grand Heritage Banquet Lawn Space",
        "description": "[Sample Catalog] Open garden venue with banquet hall suitable for weddings and milestone celebrations.",
        "category_slug": "party-venue",
        "subcategory": "Banquet Lawn",
        "platform": "Local",
        "vendor_name": "Local Heritage Crafts & Studio",
        "price": 48000.0,
        "rating": 4.7,
        "style": "Traditional",
        "tags": "venue,lawn,garden,wedding,grand-celebration,large-space",
    },
    {
        "name": "[DEMO] Fairy Light & Floral Arc Backdrop Stage",
        "description": "[Sample Catalog] Thematic pastel floral arch with neon 'Let's Celebrate' sign and fairy-light drape.",
        "category_slug": "party-decoration",
        "subcategory": "Stage Decor",
        "platform": "Local",
        "vendor_name": "Local Heritage Crafts & Studio",
        "price": 8500.0,
        "rating": 4.8,
        "style": "Bohemian",
        "tags": "decor,floral,neon,fairy-lights,backdrop,photo-stage",
    },
    {
        "name": "[DEMO] Amazon Party Balloon Garland DIY Kit",
        "description": "[Sample Catalog] 150-piece metallic gold, black, and confetti balloon garland kit with arch tape.",
        "category_slug": "party-decoration",
        "subcategory": "Balloon Decor",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 1899.0,
        "rating": 4.2,
        "style": "Modern",
        "tags": "decor,diy,balloons,gold,black,budget-friendly",
    },
    {
        "name": "[DEMO] Professional Party DJ & Sound Rig (4 Hours)",
        "description": "[Sample Catalog] Live DJ with dual JBL PA speakers, bass subwoofers, moving head disco lights & mic.",
        "category_slug": "party-entertainment",
        "subcategory": "DJ & Sound",
        "platform": "Local",
        "vendor_name": "Local Heritage Crafts & Studio",
        "price": 14000.0,
        "rating": 4.7,
        "style": "Modern",
        "tags": "music,dj,sound-system,dance-floor,lighting,entertainment",
    },
    {
        "name": "[DEMO] Candid Event Photography & 4K Teaser Reel",
        "description": "[Sample Catalog] 1 lead photographer + 1 videographer, delivering 150 edited high-res images and 60s Instagram reel.",
        "category_slug": "party-photography",
        "subcategory": "Event Photography",
        "platform": "Local",
        "vendor_name": "Local Heritage Crafts & Studio",
        "price": 18500.0,
        "rating": 4.9,
        "style": "Modern",
        "tags": "photography,candid,reels,video,drone,memories",
    },
    {
        "name": "[DEMO] AC Minibus Guest Shuttle (26-Seater, 8 Hours)",
        "description": "[Sample Catalog] Dedicated AC tempo traveler with chauffeur for guest pickup and drops within city limits.",
        "category_slug": "party-transportation",
        "subcategory": "Guest Transport",
        "platform": "Local",
        "vendor_name": "Local Heritage Crafts & Studio",
        "price": 7500.0,
        "rating": 4.4,
        "style": "Modern",
        "tags": "transportation,shuttle,bus,ac,guest-pickup",
    },
    {
        "name": "[DEMO] Eco-Friendly Biodegradable Tableware Party Pack",
        "description": "[Sample Catalog] Areca palm leaf dinner plates, wooden spoons, forks, paper cups, and cocktail napkins (100 sets).",
        "category_slug": "party-misc",
        "subcategory": "Tableware & Props",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 2499.0,
        "rating": 4.6,
        "style": "Minimalist",
        "tags": "misc,eco-friendly,tableware,palm-leaf,cutlery,sustainable",
    },

    # ------------------ JEWELRY ------------------
    {
        "name": "[DEMO] Royal Kundan & Pearl Bridal Choker Set",
        "description": "[Sample Catalog] 22K gold-plated handcrafted Kundan choker necklace embellished with dangling freshwater pearls and matching earrings.",
        "category_slug": "jewelry-necklace",
        "subcategory": "Choker Set",
        "platform": "Local",
        "vendor_name": "Local Heritage Crafts & Studio",
        "price": 32999.0,
        "rating": 4.9,
        "style": "Traditional",
        "tags": "traditional,kundan,pearls,gold-plated,wedding,bridal,choker",
    },
    {
        "name": "[DEMO] Zaveri Pearls Minimalist Rose Gold Necklace",
        "description": "[Sample Catalog] Modern cubic zirconia solitaire drop necklace with 18K rose gold plating.",
        "category_slug": "jewelry-necklace",
        "subcategory": "Minimalist Chain",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 3899.0,
        "rating": 4.4,
        "style": "Minimalist",
        "tags": "minimalist,rose-gold,cz-solitaire,cocktail,party,western",
    },
    {
        "name": "[DEMO] Handcrafted Meenakari Chandbali Earrings",
        "description": "[Sample Catalog] Traditional Rajasthani enamelled peacock chandbali earrings with emerald bead droplets.",
        "category_slug": "jewelry-earrings",
        "subcategory": "Chandbali",
        "platform": "Flipkart",
        "vendor_name": "Flipkart Retail",
        "price": 2899.0,
        "rating": 4.5,
        "style": "Traditional",
        "tags": "traditional,chandbali,meenakari,peacock,festive,ethnic",
    },
    {
        "name": "[DEMO] Clara 925 Sterling Silver Solitaire Studs",
        "description": "[Sample Catalog] Hallmarked 925 silver Swiss zircon studs with rhodium anti-tarnish coating.",
        "category_slug": "jewelry-earrings",
        "subcategory": "Silver Studs",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 1899.0,
        "rating": 4.7,
        "style": "Modern",
        "tags": "modern,silver,solitaire,office-wear,anti-tarnish,everyday",
    },
    {
        "name": "[DEMO] Giva 925 Silver Adjustable Charm Tennis Bracelet",
        "description": "[Sample Catalog] Delicate sterling silver bracelet with AAA+ grade sparkling cubic zirconia stones.",
        "category_slug": "jewelry-bracelet",
        "subcategory": "Tennis Bracelet",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 4299.0,
        "rating": 4.8,
        "style": "Modern",
        "tags": "modern,silver,tennis-bracelet,cocktail,gift,anniversary",
    },
    {
        "name": "[DEMO] Senco Gold Plated Floral Filigree Ring",
        "description": "[Sample Catalog] Adjustable statement cocktail ring featuring intricate floral jali filigree work.",
        "category_slug": "jewelry-ring",
        "subcategory": "Cocktail Ring",
        "platform": "Flipkart",
        "vendor_name": "Flipkart Retail",
        "price": 2499.0,
        "rating": 4.3,
        "style": "Traditional",
        "tags": "traditional,gold-plated,filigree,ring,cocktail,ethnic",
    },
    {
        "name": "[DEMO] Solitaire Platinum Finish Engagement Ring",
        "description": "[Sample Catalog] 1-carat moissanite look center stone mounted on 925 sterling silver band.",
        "category_slug": "jewelry-ring",
        "subcategory": "Solitaire Ring",
        "platform": "Amazon",
        "vendor_name": "Amazon India Home & Lifestyle",
        "price": 6899.0,
        "rating": 4.6,
        "style": "Modern",
        "tags": "modern,solitaire,engagement,ring,platinum-finish,silver",
    },
    {
        "name": "[DEMO] Emerald Cut Green Onyx Vintage Pendant",
        "description": "[Sample Catalog] Natural deep green onyx gemstone pendant encased in antique textured gold frame.",
        "category_slug": "jewelry-pendant",
        "subcategory": "Gemstone Pendant",
        "platform": "Local",
        "vendor_name": "Local Heritage Crafts & Studio",
        "price": 3499.0,
        "rating": 4.7,
        "style": "Bohemian",
        "tags": "bohemian,emerald-green,onyx,gold,vintage,pendant",
    },
    {
        "name": "[DEMO] Traditional Temple Jewelry Gold-Tone Kadas (Set of 2)",
        "description": "[Sample Catalog] South Indian antique matte finish temple bangles with Goddess Lakshmi carvings and ruby-red stones.",
        "category_slug": "jewelry-bangles",
        "subcategory": "Temple Kadas",
        "platform": "Local",
        "vendor_name": "Local Heritage Crafts & Studio",
        "price": 5499.0,
        "rating": 4.8,
        "style": "Traditional",
        "tags": "traditional,temple-jewelry,kada,bangles,matte-gold,wedding",
    },
]


def seed_database(db: Session = None) -> None:
    """Seed the database with vendors, categories, and products if not already present."""
    should_close = False
    if db is None:
        init_db()
        db = SessionLocal()
        should_close = True

    try:
        # 1. Seed Vendors
        logger.info("Checking Vendors...")
        vendor_map = {}
        for v_data in VENDORS_DATA:
            existing = db.query(Vendor).filter(Vendor.name == v_data["name"]).first()
            if not existing:
                vendor = Vendor(**v_data)
                db.add(vendor)
                db.flush()
                vendor_map[vendor.name] = vendor
                logger.info(f"  + Added Vendor: {vendor.name} ({vendor.platform})")
            else:
                vendor_map[existing.name] = existing

        # 2. Seed Categories
        logger.info("Checking Categories...")
        category_map = {}
        for c_data in CATEGORIES_DATA:
            existing = db.query(Category).filter(Category.slug == c_data["slug"]).first()
            if not existing:
                category = Category(**c_data)
                db.add(category)
                db.flush()
                category_map[category.slug] = category
                logger.info(f"  + Added Category: {category.name} [{category.module_type}]")
            else:
                category_map[existing.slug] = existing

        # 3. Seed Products
        logger.info("Checking Products...")
        products_added = 0
        for p_data in PRODUCTS_DATA:
            existing = db.query(Product).filter(Product.name == p_data["name"]).first()
            if not existing:
                cat = category_map.get(p_data["category_slug"])
                ven = vendor_map.get(p_data["vendor_name"])
                if not cat:
                    logger.warning(f"Category slug '{p_data['category_slug']}' not found, skipping product.")
                    continue

                product = Product(
                    name=p_data["name"],
                    description=p_data["description"],
                    category_id=cat.id,
                    subcategory=p_data["subcategory"],
                    platform=p_data["platform"],
                    vendor_id=ven.id if ven else None,
                    price=p_data["price"],
                    rating=p_data["rating"],
                    style=p_data["style"],
                    tags=p_data["tags"],
                    availability=True,
                    is_demo=True,
                )
                db.add(product)
                products_added += 1

        db.commit()
        logger.info(f"Seeding completed successfully! Total new products added: {products_added}")
        total_vendors = db.query(Vendor).count()
        total_categories = db.query(Category).count()
        total_products = db.query(Product).count()
        logger.info(f"Database totals: {total_vendors} Vendors, {total_categories} Categories, {total_products} Products.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error during database seeding: {e}")
        raise
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    logger.info("Starting PocketSmart AI database initialization and seeding...")
    seed_database()
    logger.info("Done.")
