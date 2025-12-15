{{ config(
    materialized='table',
    unique_key = 'id',
)}}

SELECT 
    neo_id,
    miss_distance_km,
    velocity_km_s,
    orbit_uncertainty,
    is_potentially_hazardous
FROM {{ ref('stg_neo_data') }}
ORDER BY
    miss_distance_km ASC,
    orbit_uncertainty DESC
LIMIT 3