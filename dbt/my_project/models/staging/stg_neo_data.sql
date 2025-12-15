{{ config(
    materialized='table',
    unique_key = 'id',
)}}

with source as (
    select*
    from {{source('raw', 'neo_data')}}
)

select
    neo_id,
    miss_distance_km,
    velocity_km_s,
    orbit_uncertainty,
    is_potentially_hazardous
from source