"""
Test Data Source Adapter
Tests S3 and Redshift data sources with fallback logic
"""

print("\n" + "=" * 60)
print("DATA SOURCE ADAPTER TEST")
print("=" * 60)

# Test 1: Configuration Check
print("\n📋 1. Configuration Check")
try:
    from backend.core.config import settings
    
    print(f"✅ Configuration loaded")
    print(f"   USE_REDSHIFT: {settings.USE_REDSHIFT}")
    print(f"   Redshift Host: {settings.REDSHIFT_HOST or 'Not configured'}")
    print(f"   S3 Bucket: {settings.S3_BUCKET_NAME}")
    print(f"   S3 Configured: {'Yes' if settings.AWS_ACCESS_KEY_ID else 'No'}")
    
except Exception as e:
    print(f"❌ Configuration error: {e}")

# Test 2: Initialize Data Source
print("\n📋 2. Initialize Data Source")
try:
    from backend.services.data_source_adapter import get_data_source
    
    source = get_data_source()
    
    print(f"✅ Data Source: {source.get_source_name()}")
    print(f"✅ Connected: {source.is_connected()}")
    
except Exception as e:
    print(f"❌ Initialization error: {e}")
    print("\n💡 Solution:")
    print("   Configure credentials in .env file:")
    print("   - For S3: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
    print("   - For Redshift: REDSHIFT_HOST, REDSHIFT_USER, REDSHIFT_PASSWORD")
    exit(1)

# Test 3: Load Patients
print("\n📋 3. Load Patients Data")
try:
    patients = source.load_patients(limit=10)
    print(f"✅ Loaded {len(patients)} patients")
    if not patients.empty:
        print(f"   Columns: {list(patients.columns)}")
        print(f"\n   Sample data:")
        if 'patient_id' in patients.columns and 'diagnosis' in patients.columns:
            for idx, row in patients.head(3).iterrows():
                print(f"   - Patient {row['patient_id']}: {row['diagnosis']}")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Load Facilities
print("\n📋 4. Load Facilities Data")
try:
    facilities = source.load_facilities()
    print(f"✅ Total facilities: {len(facilities)}")
    
    # Test filtered query
    operational = source.load_facilities(operational_only=True)
    print(f"✅ Operational facilities: {len(operational)}")
    
    if not facilities.empty:
        print(f"\n   Facilities by state:")
        if 'state' in facilities.columns:
            state_counts = facilities['state'].value_counts().head(5)
            for state, count in state_counts.items():
                print(f"   - {state}: {count} facilities")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: Load Inventory
print("\n📋 5. Load Inventory Data")
try:
    inventory = source.load_inventory()
    print(f"✅ Total inventory items: {len(inventory)}")
    
    # Test low stock filter
    low_stock = source.load_inventory(low_stock_only=True)
    print(f"⚠️ Low stock items: {len(low_stock)}")
    
    if not low_stock.empty and 'item_name' in low_stock.columns:
        print(f"\n   Critical items:")
        for idx, row in low_stock.head(5).iterrows():
            stock = row.get('stock_level', 'N/A')
            reorder = row.get('reorder_level', 'N/A')
            print(f"   - {row['item_name']}: {stock} units (reorder: {reorder})")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Test 6: Load Disease Data
print("\n📋 6. Load Disease Reports")
try:
    diseases = source.load_diseases()
    print(f"✅ Total disease records: {len(diseases)}")
    
    # Test disease filter
    malaria = source.load_diseases(disease='Malaria', months=3)
    print(f"✅ Malaria cases (3 months): {len(malaria)}")
    
    if not malaria.empty and 'cases' in malaria.columns and 'deaths' in malaria.columns:
        total_cases = malaria['cases'].sum()
        total_deaths = malaria['deaths'].sum()
        print(f"\n   Malaria statistics:")
        print(f"   - Total cases: {total_cases}")
        print(f"   - Total deaths: {total_deaths}")
        if total_cases > 0:
            death_rate = (total_deaths / total_cases * 100)
            print(f"   - Death rate: {death_rate:.2f}%")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Test 7: Load Workers
print("\n📋 7. Load Health Workers")
try:
    workers = source.load_workers()
    print(f"✅ Total workers: {len(workers)}")
    
    if not workers.empty and 'role' in workers.columns:
        print(f"\n   Workers by role:")
        role_counts = workers['role'].value_counts()
        for role, count in role_counts.head(5).items():
            print(f"   - {role}: {count}")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Test 8: Integration Test
print("\n📋 8. Integration Test - Full Workflow")
try:
    from backend.data.data_loader import DataLoader
    
    loader = DataLoader()
    datasets = loader.load_all_datasets()
    
    print(f"✅ All datasets loaded via adapter:")
    total_rows = 0
    for name, df in datasets.items():
        rows = len(df)
        total_rows += rows
        print(f"   - {name}: {rows:,} rows")
    
    print(f"\n   Total records: {total_rows:,}")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ DATA SOURCE ADAPTER TESTS COMPLETE!")
print("=" * 60)

# Show configuration summary
print("\n📋 Configuration Summary:")
print(f"   Current Source: {source.get_source_name()}")
print(f"   Connection Status: {'✅ Connected' if source.is_connected() else '❌ Disconnected'}")

if settings.USE_REDSHIFT:
    print(f"\n   Redshift Configuration:")
    print(f"   - Host: {settings.REDSHIFT_HOST or 'Not set'}")
    print(f"   - Database: {settings.REDSHIFT_DATABASE or 'Not set'}")
    print(f"   - User: {settings.REDSHIFT_USER or 'Not set'}")
else:
    print(f"\n   S3 Configuration:")
    print(f"   - Bucket: {settings.S3_BUCKET_NAME}")
    print(f"   - Region: {settings.AWS_REGION}")
    print(f"   - Credentials: {'✅ Configured' if settings.AWS_ACCESS_KEY_ID else '❌ Not configured'}")

print("\n💡 To switch data sources:")
if settings.USE_REDSHIFT:
    print("   To use S3 instead:")
    print("   1. Set USE_REDSHIFT=False in .env")
    print("   2. Restart application")
else:
    print("   To use Redshift instead:")
    print("   1. Get Redshift credentials from data team")
    print("   2. Update .env with REDSHIFT_* variables")
    print("   3. Set USE_REDSHIFT=True")
    print("   4. Restart application")

print("\n" + "=" * 60 + "\n")