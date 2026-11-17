import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from certificates.models import Certificate
from donations.models import Donation
from gamification.models import Badge, PointsLedger, Rating, UserBadge
from logistics.models import Claim, DeliveryTask, FoodSafetyChecklist, StatusEvent

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds comprehensive demo data for AnnaSetu (30 donors, 15 NGOs, 25 volunteers, 200 donations)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding AnnaSetu demo data..."))

        # 1. Superuser
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@annasetu.org",
                "is_staff": True,
                "is_superuser": True,
                "role": User.Role.DONOR,
                "organization_name": "AnnaSetu Foundation HQ",
                "is_verified": True,
                "reliability_score": 5.0,
            }
        )
        admin_user.set_password("admin123")
        admin_user.save()

        # 2. Badges
        badges_data = [
            {"slug": "first-rescue", "name": "First Rescue", "description": "Completed first verified food delivery", "icon": "award", "color": "#16A34A", "points_reward": 25},
            {"slug": "night-owl", "name": "Night Owl", "description": "Rescued wedding banquet surplus after 10 PM", "icon": "moon", "color": "#F59E0B", "points_reward": 50},
            {"slug": "century-club", "name": "100 Meals", "description": "Delivered over 100 meals to hungry bellies", "icon": "shield-check", "color": "#3B82F6", "points_reward": 100},
            {"slug": "five-star", "name": "Reliability Icon", "description": "Maintained a 5.0★ reliability score across 10 handoffs", "icon": "star", "color": "#8B5CF6", "points_reward": 75},
        ]
        badge_objs = []
        for bd in badges_data:
            b, _ = Badge.objects.get_or_create(slug=bd["slug"], defaults=bd)
            badge_objs.append(b)

        # Coordinates bounding box: Delhi NCR & Bareilly
        city_coords = [
            (28.6139, 77.2090, "Connaught Place, New Delhi"),
            (28.5355, 77.3910, "Sector 62, Noida"),
            (28.4595, 77.0266, "Cyber City, Gurugram"),
            (28.7041, 77.1025, "Pitampura, North Delhi"),
            (28.3670, 79.4304, "Civil Lines, Bareilly"),
            (28.3550, 79.4120, "Model Town, Bareilly"),
            (28.5244, 77.2066, "Hauz Khas, New Delhi"),
            (28.6304, 77.2177, "Barakhamba Road, New Delhi"),
        ]

        # 3. Create Donors (30)
        donors = []
        donor_demo, _ = User.objects.get_or_create(
            username="donor_demo",
            defaults={
                "email": "donor@annasetu.org",
                "role": User.Role.DONOR,
                "organization_name": "Royal Treat Banquets & Catering",
                "phone": "+91 98765 43210",
                "address": "Connaught Place, New Delhi",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "is_verified": True,
                "reliability_score": 4.9,
            }
        )
        donor_demo.set_password("password123")
        donor_demo.save()
        donors.append(donor_demo)

        donor_orgs = [
            "Haldiram's Express", "Bikanervala Sweets", "Barbeque Nation",
            "Taj Palace Banquets", "Sagar Ratna", "Punjab Grill",
            "Biryani By Kilo", "The Big Chill Cafe", "Saravana Bhavan",
            "ITC Maurya Kitchens", "Gulati Spice Kitchen", "Pind Balluchi",
            "Moti Mahal Delux", "Karim's Restaurant", "Radisson Blu Kitchens",
            "Hyatt Regency Banquets", "JW Marriott Kitchen", "Chumbak Cafe",
            "Social Offline", "Farzi Cafe", "Mamagoto", "Nirula's",
            "Aggarwal Sweets", "Chai Point Corporate", "Olive Bar & Kitchen",
            "Smoke House Deli", "Cafe Delhi Heights", "Kake Da Hotel", "Nathu's Sweets"
        ]

        for i, org_name in enumerate(donor_orgs):
            lat, lon, addr = random.choice(city_coords)
            u, _ = User.objects.get_or_create(
                username=f"donor_{i+1}",
                defaults={
                    "email": f"donor_{i+1}@annasetu.org",
                    "role": User.Role.DONOR,
                    "organization_name": org_name,
                    "phone": f"+91 9811{random.randint(100000, 999999)}",
                    "address": addr,
                    "latitude": lat + random.uniform(-0.04, 0.04),
                    "longitude": lon + random.uniform(-0.04, 0.04),
                    "is_verified": True,
                    "reliability_score": round(random.uniform(4.2, 5.0), 2),
                }
            )
            u.set_password("password123")
            u.save()
            donors.append(u)

        # 4. Create NGOs (15)
        ngos = []
        ngo_demo, _ = User.objects.get_or_create(
            username="ngo_demo",
            defaults={
                "email": "ngo@annasetu.org",
                "role": User.Role.NGO,
                "organization_name": "Robin Hood Army - Delhi North",
                "phone": "+91 98765 00001",
                "address": "Model Town, Bareilly",
                "latitude": 28.3670,
                "longitude": 79.4304,
                "is_verified": True,
                "capacity_servings_per_day": 500,
                "accepts_veg_only": False,
                "service_radius_km": 15.0,
                "reliability_score": 4.8,
            }
        )
        ngo_demo.set_password("password123")
        ngo_demo.save()
        ngos.append(ngo_demo)

        ngo_names = [
            "Goonj Feeding Center", "Annamrita Community Kitchen", "Feeding India Hunger Relief",
            "Akshaya Patra Delhi Hub", "Uday Foundation", "Smile Foundation Nutrition",
            "Khalsa Aid Food Truck", "Roti Bank Bareilly", "Pratham Shiksha Kitchen",
            "Asha Deep Community Shelter", "Care India Kitchen", "Hope Welfare Trust",
            "Goonj Bareilly Depot", "Seva Bharati Kitchens"
        ]

        for i, ngo_title in enumerate(ngo_names):
            lat, lon, addr = random.choice(city_coords)
            u, _ = User.objects.get_or_create(
                username=f"ngo_{i+1}",
                defaults={
                    "email": f"ngo_{i+1}@annasetu.org",
                    "role": User.Role.NGO,
                    "organization_name": ngo_title,
                    "phone": f"+91 9822{random.randint(100000, 999999)}",
                    "address": addr,
                    "latitude": lat + random.uniform(-0.03, 0.03),
                    "longitude": lon + random.uniform(-0.03, 0.03),
                    "is_verified": True,
                    "capacity_servings_per_day": random.choice([200, 350, 500, 1000]),
                    "accepts_veg_only": random.choice([True, False]),
                    "service_radius_km": random.choice([10.0, 15.0, 20.0]),
                    "reliability_score": round(random.uniform(4.3, 5.0), 2),
                }
            )
            u.set_password("password123")
            u.save()
            ngos.append(u)

        # 5. Create Volunteers (25)
        volunteers = []
        vol_demo, _ = User.objects.get_or_create(
            username="volunteer_demo",
            defaults={
                "email": "volunteer@annasetu.org",
                "role": User.Role.VOLUNTEER,
                "first_name": "Aarav",
                "last_name": "Sharma",
                "phone": "+91 99999 88888",
                "address": "Pitampura, North Delhi",
                "latitude": 28.7041,
                "longitude": 77.1025,
                "is_verified": True,
                "reliability_score": 4.9,
            }
        )
        vol_demo.set_password("password123")
        vol_demo.save()
        volunteers.append(vol_demo)

        vol_names = [
            ("Rohan", "Verma"), ("Priya", "Patel"), ("Ananya", "Deshmukh"),
            ("Vikram", "Malhotra"), ("Sneha", "Gupta"), ("Kunal", "Bansal"),
            ("Divya", "Iyer"), ("Aditya", "Nair"), ("Meera", "Reddy"),
            ("Kabir", "Mehta"), ("Tanvi", "Jain"), ("Arjun", "Kapoor"),
            ("Ishaan", "Bhatia"), ("Rhea", "Chauhan"), ("Siddharth", "Rao"),
            ("Aniket", "Sood"), ("Pooja", "Mishra"), ("Kavita", "Saxena"),
            ("Nikhil", "Trivedi"), ("Swati", "Pandey"), ("Manish", "Goyal"),
            ("Neha", "Tyagi"), ("Gaurav", "Dubey"), ("Shruti", "Aggarwal")
        ]

        for i, (fn, ln) in enumerate(vol_names):
            lat, lon, addr = random.choice(city_coords)
            u, _ = User.objects.get_or_create(
                username=f"volunteer_{i+1}",
                defaults={
                    "email": f"vol_{i+1}@annasetu.org",
                    "role": User.Role.VOLUNTEER,
                    "first_name": fn,
                    "last_name": ln,
                    "phone": f"+91 9833{random.randint(100000, 999999)}",
                    "address": addr,
                    "latitude": lat + random.uniform(-0.04, 0.04),
                    "longitude": lon + random.uniform(-0.04, 0.04),
                    "is_verified": True,
                    "reliability_score": round(random.uniform(4.4, 5.0), 2),
                }
            )
            u.set_password("password123")
            u.save()
            volunteers.append(u)

        # 6. Create 200 Donations spread across the last 90 days
        food_titles = [
            "Fresh Dal Makhani & Jeera Rice", "Shahi Paneer with Tandoori Rotis",
            "Vegetable Pulao with Raita", "Mix Veg Curry and Puris",
            "Chole Bhature Lunch Leftover", "Assorted Sandwiches & Rolls",
            "Steamed Idli and Sambhar", "Pav Bhaji (Bulk Batch)",
            "Kadhai Paneer & Naan Bread", "Chicken Biryani Banquet Trays",
            "Butter Chicken & Rumali Roti", "Rajma Chawal Family Trays",
            "Khichdi & Aloo Gobhi", "Matar Paneer with Parathas",
            "Mutton Biryani Buffet Remaining", "Fresh Samosas & Kachoris",
            "Fruit Custard & Gulab Jamun", "Hakko Noodles & Manchurian"
        ]

        now = timezone.now()
        statuses_distribution = (
            [Donation.Status.DELIVERED] * 140
            + [Donation.Status.POSTED] * 25
            + [Donation.Status.CLAIMED] * 15
            + [Donation.Status.ASSIGNED] * 10
            + [Donation.Status.PICKED_UP] * 5
            + [Donation.Status.EXPIRED] * 5
        )

        created_count = 0
        for i in range(200):
            donor = random.choice(donors)
            status = statuses_distribution[i]
            days_ago = random.randint(0, 90) if status == Donation.Status.DELIVERED else random.randint(0, 3)
            created_at = now - timedelta(days=days_ago, hours=random.randint(1, 12))

            # Expiry time
            safe_until = created_at + timedelta(hours=random.choice([4, 6, 8, 12]))
            if status == Donation.Status.POSTED:
                # Keep active for next few hours
                safe_until = now + timedelta(hours=random.randint(2, 6))

            title = random.choice(food_titles)
            food_type = Donation.FoodType.NONVEG if "Chicken" in title or "Mutton" in title else Donation.FoodType.VEG
            servings = random.randint(20, 250)

            lat = donor.latitude or 28.6139
            lon = donor.longitude or 77.2090

            donation = Donation.objects.create(
                donor=donor,
                title=title,
                description="Fresh surplus prepared with care. Packed in sanitized containers.",
                food_type=food_type,
                is_cooked=True,
                quantity_servings=servings,
                pickup_address=donor.address or "Central Delhi Kitchen",
                latitude=lat + random.uniform(-0.015, 0.015),
                longitude=lon + random.uniform(-0.015, 0.015),
                pickup_from=created_at,
                safe_until=safe_until,
                status=status,
            )
            # Override auto_now_add for historical distribution
            Donation.objects.filter(pk=donation.pk).update(created_at=created_at)

            # Audit status event: Posted
            StatusEvent.objects.create(
                donation=donation,
                from_status="none",
                to_status=Donation.Status.POSTED,
                actor=donor,
                timestamp=created_at,
            )

            # If claimed or further, create claim & task
            if status in [Donation.Status.CLAIMED, Donation.Status.ASSIGNED, Donation.Status.PICKED_UP, Donation.Status.DELIVERED]:
                ngo = random.choice(ngos)
                claim = Claim.objects.create(
                    donation=donation,
                    ngo=ngo,
                    status=Claim.Status.ACCEPTED,
                    servings_requested=servings,
                    note="We will distribute this to our shelter kitchen.",
                )
                Claim.objects.filter(pk=claim.pk).update(created_at=created_at + timedelta(minutes=20))

                volunteer = random.choice(volunteers) if status != Donation.Status.CLAIMED else None
                task_status = {
                    Donation.Status.CLAIMED: DeliveryTask.Status.PENDING,
                    Donation.Status.ASSIGNED: DeliveryTask.Status.ASSIGNED,
                    Donation.Status.PICKED_UP: DeliveryTask.Status.PICKED_UP,
                    Donation.Status.DELIVERED: DeliveryTask.Status.DELIVERED,
                }[status]

                task = DeliveryTask.objects.create(
                    donation=donation,
                    claim=claim,
                    volunteer=volunteer,
                    status=task_status,
                    distance_km=round(random.uniform(2.5, 14.0), 1),
                )

                if status in [Donation.Status.PICKED_UP, Donation.Status.DELIVERED]:
                    task.picked_up_at = created_at + timedelta(hours=1)
                    task.save(update_fields=["picked_up_at"])
                    FoodSafetyChecklist.objects.create(
                        task=task,
                        temperature_ok=True,
                        packaging_ok=True,
                        smell_ok=True,
                        within_safe_time=True,
                        completed_by=volunteer,
                    )

                if status == Donation.Status.DELIVERED:
                    delivered_time = created_at + timedelta(hours=2)
                    task.delivered_at = delivered_time
                    task.save(update_fields=["delivered_at"])

                    # Points ledger for volunteer
                    if volunteer:
                        PointsLedger.objects.create(
                            user=volunteer,
                            points=random.choice([15, 20, 25]),
                            source=PointsLedger.Source.DELIVERY,
                            description=f"Delivered {title}",
                            task=task,
                        )

                    # Rating
                    Rating.objects.create(
                        from_user=ngo,
                        to_user=donor,
                        task=task,
                        score=random.choice([4, 5]),
                        comment="Excellent food quality and seamless handoff!",
                    )

                    # Certificate
                    Certificate.objects.create(
                        donor=donor,
                        donation=donation,
                        cert_type=Certificate.CertType.PER_DONATION,
                        total_servings=servings,
                        total_kg=round(servings * 0.4, 1),
                        co2_avoided_kg=round(servings * 0.4 * 2.5, 1),
                    )

            created_count += 1

        # Award some badges to volunteers
        for vol in volunteers[:10]:
            UserBadge.objects.get_or_create(user=vol, badge=badge_objs[0])
            if random.random() > 0.5:
                UserBadge.objects.get_or_create(user=vol, badge=badge_objs[1])

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} donations, 30 donors, 15 NGOs, and 25 volunteers!"))
        self.stdout.write(self.style.SUCCESS("Demo logins:"))
        self.stdout.write(self.style.SUCCESS("  Admin:      admin / admin123"))
        self.stdout.write(self.style.SUCCESS("  Donor:      donor_demo / password123"))
        self.stdout.write(self.style.SUCCESS("  NGO:        ngo_demo / password123"))
        self.stdout.write(self.style.SUCCESS("  Volunteer:  volunteer_demo / password123"))
