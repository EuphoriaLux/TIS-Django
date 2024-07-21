from .models import CruiseCompany, CruiseType, Brand, Cruise, CruiseCategory, CruiseSession
from django.utils import timezone
from datetime import timedelta

def create_initial_data():
    # Create CruiseCompany instances
    company1 = CruiseCompany.objects.create(
        name="Royal Caribbean International",
        description="A global cruise company known for innovative ships, exciting destinations and world-renowned service.",
        website="https://www.royalcaribbean.com/"
    )
    company2 = CruiseCompany.objects.create(
        name="Norwegian Cruise Line",
        description="Offering freestyle cruising with a variety of dining and entertainment options.",
        website="https://www.ncl.com/"
    )

    # Create CruiseType instances
    type1 = CruiseType.objects.create(
        name="Caribbean",
        description="Tropical paradise cruises featuring white sandy beaches and crystal-clear waters."
    )
    type2 = CruiseType.objects.create(
        name="Mediterranean",
        description="Explore rich history, diverse cultures, and beautiful coastlines of the Mediterranean."
    )

    # Create Brand instances
    brand1 = Brand.objects.create(
        name="Royal Caribbean",
        description="Award-winning cruise line known for innovation at sea",
        website="https://www.royalcaribbean.com/",
        featured=True
    )
    brand2 = Brand.objects.create(
        name="Norwegian",
        description="Freestyle cruising with a modern fleet",
        website="https://www.ncl.com/",
        featured=True
    )

    # Create Cruise instances
    cruise1 = Cruise.objects.create(
        name="Caribbean Paradise",
        description="7-night cruise to the Eastern Caribbean",
        cruise_type=type1,
        company=company1,
        image_url="https://example.com/caribbean_cruise.jpg"
    )
    cruise2 = Cruise.objects.create(
        name="Mediterranean Adventure",
        description="10-night cruise exploring the best of the Mediterranean",
        cruise_type=type2,
        company=company2,
        image_url="https://example.com/mediterranean_cruise.jpg"
    )

    # Create CruiseCategory instances
    CruiseCategory.objects.create(
        cruise=cruise1,
        name="Interior",
        description="Cozy interior stateroom",
        price=799.99
    )
    CruiseCategory.objects.create(
        cruise=cruise1,
        name="Ocean View",
        description="Stateroom with ocean view",
        price=999.99
    )
    CruiseCategory.objects.create(
        cruise=cruise2,
        name="Balcony",
        description="Stateroom with private balcony",
        price=1299.99
    )
    CruiseCategory.objects.create(
        cruise=cruise2,
        name="Suite",
        description="Luxurious suite with separate living area",
        price=1999.99
    )

    # Create CruiseSession instances
    start_date = timezone.now().date() + timedelta(days=30)
    CruiseSession.objects.create(
        cruise=cruise1,
        start_date=start_date,
        end_date=start_date + timedelta(days=7),
        capacity=2000
    )
    CruiseSession.objects.create(
        cruise=cruise2,
        start_date=start_date + timedelta(days=14),
        end_date=start_date + timedelta(days=24),
        capacity=2500
    )

    print("Initial data created successfully!")
