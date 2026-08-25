import asyncio
import time
import httpx
import os
import subprocess
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

def get_pg_stats():
    try:
        out = subprocess.check_output([
            "docker", "exec", "sentinel-razorpay-buildathon-postgres-1",
            "psql", "-U", "postgres", "-d", "sentinel", "-t", "-c",
            "SELECT state, count(*) FROM pg_stat_activity WHERE datname = 'sentinel' GROUP BY state;"
        ]).decode('utf-8')
        active = 0
        idle = 0
        for line in out.split('\n'):
            if 'active' in line:
                active += int(line.split('|')[1].strip())
            elif 'idle' in line:
                idle += int(line.split('|')[1].strip())
        return {"pg_active": active, "pg_idle": idle, "pg_total": active+idle}
    except Exception as e:
        return {"pg_error": str(e)}

def get_redis_stats():
    try:
        r = redis.from_url(REDIS_URL)
        info = r.info()
        return {
            "redis_clients": info.get("connected_clients", 0),
            "redis_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
            "redis_used_memory_human": info.get("used_memory_human", "0")
        }
    except Exception as e:
        return {"redis_error": str(e)}

def get_docker_stats():
    try:
        out = subprocess.check_output(
            ["docker", "stats", "--no-stream", "--format", "{{.Name}},{{.CPUPerc}},{{.MemUsage}}"]
        ).decode('utf-8')
        stats = {}
        for line in out.strip().split('\n'):
            if line:
                parts = line.split(',')
                if len(parts) >= 3:
                    name = parts[0]
                    cpu = parts[1]
                    mem = parts[2]
                    if "api" in name or "worker" in name or "postgres" in name or "redis" in name:
                        stats[name] = {"cpu": cpu, "mem": mem}
        return stats
    except Exception as e:
        return {"docker_error": str(e)}

async def monitor():
    print("Starting Saturation Monitor...")
    max_pg_total = 0
    max_redis_clients = 0
    max_api_cpu = 0.0
    
    for _ in range(30):
        pg = get_pg_stats()
        r = get_redis_stats()
        d = get_docker_stats()
        
        print(f"PG: {pg}")
        print(f"Redis: {r}")
        for k, v in d.items():
            if "api" in k or "worker" in k:
                print(f"{k}: {v}")
                
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(monitor())
