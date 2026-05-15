from fastapi import FastAPI
import time
import redis
import json

app = FastAPI()

# --- Redis connection ---
r = redis.Redis(
    host="jmc-redis-master.redis.svc.cluster.local",  #"jmc-redis-master.redis.svc.cluster.local" # 172.16.0.4 works from outside the cluster with IP.
    port= 6379, #30952,-> this is the nodePort to acces from outside cluster. TESTING the commit...
    decode_responses=True
)

# Simulated DB latency
def fake_db(product_id: int):
    time.sleep(0.8)  # 800ms DB delay
    return {
        "id": product_id,
        "name": "Gaming Laptop",
        "price": 5000
    }

# --- CACHE ASIDE PATTERN ---
@app.get("/product/{product_id}")
def get_product(product_id: int):

    start = time.time()

    cache_key = f"product:{product_id}"

    # 1. Check Redis first
    cached = r.get(cache_key)

    if cached:
        return {
            "source": "redis-cache",
            "data": json.loads(cached),
            "response_time_ms": round((time.time() - start) * 1000, 2)
        }

    # 2. Cache miss → DB
    data = fake_db(product_id)

    # 3. Save to Redis
    r.setex(cache_key, 60, json.dumps(data))

    return {
        "source": "database",
        "data": data,
        "response_time_ms": round((time.time() - start) * 1000, 2)
    }