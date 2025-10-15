"""
Test Data Module
Tests symptom database and data loader
"""

print("\n" + "=" * 60)
print("TESTING DATA MODULE")
print("=" * 60)

# Test 1: Symptom Database
print("\n📋 1. Symptom Database")
try:
    from backend.data.symptom_database import (
        get_disease_info,
        search_disease_by_symptoms,
        SUPPORTED_LANGUAGES,
        SUPPORTED_DISEASES
    )
    
    print(f"✅ Supported languages: {len(SUPPORTED_LANGUAGES)}")
    print(f"✅ Supported diseases: {len(SUPPORTED_DISEASES)}")
    
    # Test getting disease info
    malaria_info = get_disease_info("malaria", "english")
    print(f"✅ Malaria symptoms: {len(malaria_info['symptoms'])}")
    
    # Test in Hausa
    malaria_hausa = get_disease_info("malaria", "hausa")
    print(f"✅ Malaria (Hausa): {malaria_hausa['disease_name']}")
    
    # Test symptom search
    results = search_disease_by_symptoms(["fever", "headache"], "english")
    print(f"✅ Found {len(results)} diseases matching symptoms")
    
except Exception as e:
    print(f"❌ Symptom database error: {e}")

# Test 2: Data Loader
print("\n📋 2. Data Loader")
try:
    from backend.data.data_loader import DataLoader
    
    loader = DataLoader()
    
    print("  Loading datasets from S3...")
    datasets = loader.load_all_datasets()
    
    print(f"✅ Loaded {len(datasets)} datasets:")
    for name, df in datasets.items():
        print(f"   - {name}: {len(df)} rows")
    
except Exception as e:
    print(f"❌ Data loader error: {e}")

# Test 3: Facility Info
print("\n📋 3. Facility Information")
try:
    facilities_df = loader.get_dataset('facilities')
    
    if not facilities_df.empty:
        # Get first facility
        facility_id = facilities_df.iloc[0]['facility_id']
        facility = loader.get_facility_info(facility_id)
        
        print(f"✅ Facility ID: {facility_id}")
        print(f"   Name: {facility.get('facility_name', 'N/A')}")
        print(f"   State: {facility.get('state', 'N/A')}")
        print(f"   Status: {facility.get('operational_status', 'N/A')}")
    else:
        print("⚠️ No facilities data available")
    
except Exception as e:
    print(f"❌ Facility info error: {e}")

# Test 4: Inventory Status
print("\n📋 4. Inventory Status")
try:
    inventory = loader.get_inventory_status(low_stock_only=True)
    
    print(f"✅ Low stock items: {len(inventory)}")
    
    if not inventory.empty:
        critical = inventory[inventory['status'] == 'Critical']
        print(f"   Critical: {len(critical)}")
        print(f"   Low: {len(inventory[inventory['status'] == 'Low'])}")
        
        # Show a few examples
        print("\n   Examples of low stock items:")
        for idx, row in inventory.head(3).iterrows():
            print(f"   - {row['item_name']}: {row['stock_level']} units ({row['status']})")
    
except Exception as e:
    print(f"❌ Inventory error: {e}")

# Test 5: Disease Statistics
print("\n📋 5. Disease Statistics")
try:
    diseases = loader.get_disease_statistics(disease='Malaria', months=6)
    
    if not diseases.empty:
        total_cases = diseases['cases'].sum()
        total_deaths = diseases['deaths'].sum()
        
        print(f"✅ Malaria (last 6 months):")
        print(f"   Total cases: {total_cases}")
        print(f"   Total deaths: {total_deaths}")
        print(f"   Facilities reporting: {diseases['facility_id'].nunique()}")
    else:
        print("⚠️ No disease data available")
    
except Exception as e:
    print(f"❌ Disease statistics error: {e}")

# Test 6: Dashboard Summary
print("\n📋 6. Dashboard Summary")
try:
    summary = loader.get_dashboard_summary()
    
    print(f"✅ Dashboard metrics:")
    print(f"   Total facilities: {summary.get('total_facilities', 0)}")
    print(f"   Operational: {summary.get('operational_facilities', 0)}")
    print(f"   Total patients: {summary.get('total_patients', 0)}")
    print(f"   Low stock items: {summary.get('low_stock_items', 0)}")
    print(f"   Health workers: {summary.get('total_health_workers', 0)}")
    
    # Recent patient stats
    recent = summary.get('recent_patient_stats', {})
    print(f"\n   Last 7 days:")
    print(f"   - Patient visits: {recent.get('total_visits', 0)}")
    print(f"   - Average age: {recent.get('avg_age', 0)}")
    
except Exception as e:
    print(f"❌ Dashboard summary error: {e}")

print("\n" + "=" * 60)
print("✅ DATA MODULE TESTS COMPLETE!")
print("=" * 60 + "\n")