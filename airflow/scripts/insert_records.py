import os
import psycopg2
from api_request import fetch_data, fetch_orbital_data

POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

def connect_to_db():
    print("Connecting to the PostgreSQL database...")
    try:
        conn = psycopg2.connect(
            host = POSTGRES_DB,
            port = 5432,
            dbname = POSTGRES_DB,
            user = POSTGRES_USER,
            password = POSTGRES_PASSWORD
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        raise 
    
def create_table(conn):
    print("Creating table if not exist...")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS raw;
            CREATE TABLE IF NOT EXISTS raw.neo_data (
                neo_id VARCHAR(50) PRIMARY KEY,
                miss_distance_km FLOAT,
                velocity_km_s FLOAT,
                orbit_uncertainty VARCHAR(10),
                is_potentially_hazardous BOOLEAN,
                inserted_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        print("Table was created.")
    except psycopg2.Error as e:
        print(f"Failed to create table: {e}")
        raise

def insert_records(conn, orbital_responses):
    print("Inserting data into database.")
    try:
        cursor = conn.cursor()
        inserted_count = 0

        for i, resp in enumerate(orbital_responses, 1):
            neo_id = resp.get('id')

            # Get close approach data (use first one)
            close_approach_data = resp.get('close_approach_data', [])
            if not close_approach_data:
                print(f"\nNo close approach data for {neo_id}")
                continue

            close_approach = close_approach_data[0]

            # Extract the 5 fields we need
            is_hazardous = resp.get('is_potentially_hazardous_asteroid')
            miss_distance_km = close_approach.get('miss_distance', {}).get('kilometers')
            velocity_km_s = close_approach.get('relative_velocity', {}).get('kilometers_per_second')
            orbital_data = resp.get('orbital_data', {})
            orbit_uncertainty = orbital_data.get('orbit_uncertainty')
            
            # Insert into database- handles if id exists 
            try:
                cursor.execute("""
                    INSERT INTO raw.neo_data (
                        neo_id,
                        miss_distance_km,
                        velocity_km_s,
                        orbit_uncertainty,
                        is_potentially_hazardous
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (neo_id) 
                    DO UPDATE SET
                        miss_distance_km = EXCLUDED.miss_distance_km,
                        velocity_km_s = EXCLUDED.velocity_km_s,
                        orbit_uncertainty = EXCLUDED.orbit_uncertainty,
                        is_potentially_hazardous = EXCLUDED.is_potentially_hazardous,
                        inserted_at = NOW()
                """, (
                    neo_id,
                    float(miss_distance_km) if miss_distance_km else None,
                    float(velocity_km_s) if velocity_km_s else None,
                    orbit_uncertainty,
                    is_hazardous
                ))
                inserted_count += 1
                
            except psycopg2.Error as e:
                print(f"\nError inserting record {neo_id}: {e}")
                continue
        
        conn.commit()
        print(f"\nSuccessfully inserted/updated {inserted_count} records.")
        return inserted_count
        
    except psycopg2.Error as e:
        print(f"Error inserting data: {e}")
        conn.rollback()
        raise

def main():
    try:
        print("Fetching NEO data from NASA API...")
        base_data = fetch_data()

        # Get all unique id's for search API
        asteroid_ids = set() # set enforces no dups and order doesn't matter here, also O(n)
        for date, a_ids in base_data['near_earth_objects'].items():
            for id in a_ids:
                asteroid_ids.add(id['id'])
        
        print(f"Fetching orbital data for {len(asteroid_ids)} asteroids...")
        orbital_responses = []
        for i, n_id in enumerate(asteroid_ids, 1):
            orb_resp = fetch_orbital_data(n_id)
            if orb_resp:
                orbital_responses.append(orb_resp)

        print(f"\nCollected {len(orbital_responses)} orbital responses.")
        
         # Connect to database
        conn = connect_to_db()
        
        # Create table
        create_table(conn)
        
        # Insert records from the list
        insert_records(conn, orbital_responses)
        
    except Exception as e:
        print(f"An error occurred during execution: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
