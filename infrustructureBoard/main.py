import os
import time
import requests
import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="Infrastructure Monitor")

#Configuratiion for frontend to talk to the backend
# Allows GET, POST, OPTIONS, HEADERS and origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check route to see if the server is running"""
    return {"status": "online", "message": "Monitoring Active"}

#hardware metrics collection section
def hardware_metrics() ->dict:

    cpu_percent = psutil.cpu_percent(interval=None)

    ram = psutil.virtual_memory()

    disk_path = "C:\\" if os.name == "nt" else "/"
    disk = psutil.disk_usage(disk_path)

    return {
        "cpu": {
            "cpu_usage": cpu_percent,
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False)
        },
        "ram": {
            "usage_percent": ram.percent,
            "used_gb": round(ram.used / (1024 ** 3), 2),
            "total_gb": round(ram.total / (1024 ** 3), 2)
        },
        "disk": {
            "disk_usage": disk.percent,
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "total_gb": round(disk.total / (1024 ** 3), 2)
        }
    }


#Network endpoint health section
endpoints = [
    {"name": "google", "url": "https://www.google.com"},
    {"name": "GitHub", "url": "https://github.com"},
    {"name": "Cloudflare DNS", "url": "https://1.1.1.1"},
    {"name": "Simulated 500 Error", "url": "https://httpbin.org/status/500"},
    {"name": "Invalid Domain", "url": "https://this-domain-does-not-exist-test.org"}
]

#pings URL, finds latency and catches connection errors
def check_endpoint(name: str, url: str, timeout_sec: float = 3.0) -> dict:
    start_time = time.perf_counter()

    try:
        response= requests.get(url, timeout=timeout_sec)
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        code = response.status_code

        # status codes
        if 200 <= code < 400:
            status = "UP"
        elif 400 <= code < 500:
            status = "ERROR"
        else:
            status = "DEGRADED"

        return {
            "name": name,
            "url": url,
            "status": status,
            "code": code,
            "latency": latency,
            "error": None
        }

    except requests.exceptions.Timeout:
        return{
            "name": name,
            "url": url,
            "status": "TIMEOUT",
            "code": 0,
            "latency": round(timeout_sec * 1000, 2),
            "error": "Request timed out"
        }
    except requests.exceptions.ConnectionError as e:
        return{
            "name": name,
            "url": url,
            "status": "DOWN",
            "code": 0,
            "latency": None,
            "error": str(e)
        }

#Provide routes for front end to fetch data

#fetch hardware metrics
@app.get("/api/metrics/hardware")
def api_hardware():
    return hardware_metrics()

#
@app.get("/api/metrics/network")
def api_network():
    results = [check_endpoint(site["name"], site["url"]) for site in endpoints]
    total = len(results)
    online = sum(1 for i in results if i["status"] == "UP")

    return{
        "summary": {
            "total": total,
            "online": online,
            "uptime_percent": round((online / total) * 100, 1) if total > 0 else 0

        },
        "endpoints": results
    }

@app.get("/api/metrics")
def dashboard_metrics():
    return{
        "timestamp": time.time(),
        "hardware": api_hardware(),
        "network": api_network()
    }