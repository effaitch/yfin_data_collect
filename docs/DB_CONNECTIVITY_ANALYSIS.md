# PostgreSQL Connectivity Analysis - Across All Services
**Generated:** March 23, 2026  
**Context:** Security hardening changed PostgreSQL bind addresses

---

## Executive Summary

After PostgreSQL bind address changes:
- **Port 5432**: Bound to `127.0.0.1` only (host-local)
- **Port 55432**: Bound to `0.0.0.0` (accessible to all interfaces)

All services have been configured to use `localhost:55432`, but **Docker containers using bridge networking cannot reach localhost on the host**. This is the same issue that affected `ig-stream`.

---

## Current PostgreSQL Network Configuration

```bash
# Active PostgreSQL listeners:
LISTEN 0.0.0.0:55432       # Public interface (accessible from containers)
LISTEN 127.0.0.1:5432      # Host-local only (NOT accessible from containers)
LISTEN [::]:55432          # IPv6 public
```

**Key Finding:** Port 55432 is already bound to `0.0.0.0`, so it IS accessible from Docker containers - they just can't use "localhost" to reach it.

---

## Services Requiring Review

### ✅ 1. yfin_data_collect (Current Project)
**Status:** ✅ **NO DOCKER - Running natively on host**

**Configuration:**
```env
DB_HOST=localhost
DB_PORT=55432
```

**Deployment:**
- Runs via cron job: `0 2 * * 6 /home/farq/projects/yfin_data_collect/run_weekend_job.sh`
- Executes natively on host (not containerized)
- Script: `src/backfill_combined_csv_local.py`

**Connectivity:** ✅ **WORKING**
- Native host process can use `localhost:55432` without issues
- No Docker networking involved

**Action Required:** ✅ **NONE** - Already working correctly

---

### ⚠️ 2. igTrade_api (ig-stream service)
**Status:** ✅ **FIXED** - Now using host networking

**Configuration:**
```yaml
# docker-compose.yml
network_mode: host
```

**Cron Jobs:**
- `0 20 * * 6` - `cron_upload_data.sh` (weekly CSV backfill)
- `0 2 * * 0` - `cron_download_historical.sh`
- `0 3 * * 0` - `cron_upload_historical.sh`
- `*/10 * * * 1-5` - `auto_restart_monitor.sh`

**Connectivity:**
- ✅ Container: **WORKING** - Switched to host networking
- ✅ Cron scripts: **WORKING** - Run natively on host

**Action Required:** ✅ **NONE** - Already fixed with host networking

---

### ⚠️ 3. binance_live_data
**Status:** ⚠️ **POTENTIAL ISSUE**

**Configuration:**
```yaml
# docker-compose.yml
networks:
  default:
    driver: bridge  # ⚠️ BRIDGE MODE
```

```env
# .env
DB_HOST=localhost  # ⚠️ Won't work from container
DB_PORT=55432
```

**Cron Jobs:**
- `0 * * * *` - `upload_to_postgres.py` (hourly)

**Running Containers:**
- `binance_collector` - Using `binance_live_data_default` network (bridge)

**Connectivity:**
- ⚠️ Container: **LIKELY BROKEN** - Bridge mode + `localhost` won't work
- ✅ Cron script: **WORKING** - Runs natively on host via `./venv/bin/python`

**Action Required:**
Choose one of these solutions:

**Option A: Switch to host networking (RECOMMENDED - matches igTrade_api pattern)**
```yaml
# docker-compose.yml
services:
  binance_collector:
    network_mode: host
```

**Option B: Use host gateway IP**
```yaml
# docker-compose.yml
services:
  binance_collector:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```
```env
DB_HOST=host.docker.internal
DB_PORT=55432
```

**Option C: Use host's actual network interface IP**
```env
DB_HOST=172.17.0.1  # Docker bridge gateway (or actual host IP)
DB_PORT=55432
```

---

### ⚠️ 4. collector_manager
**Status:** ⚠️ **POTENTIAL ISSUE**

**Configuration:**
```yaml
# docker-compose.yml
networks:
  collector_network:
    driver: bridge  # ⚠️ BRIDGE MODE
```

```env
# .env
DB_HOST=localhost  # ⚠️ Won't work from container
DB_PORT=55432
```

**Cron Jobs:**
- `0 6 * * *` - `update_data_lake.sh` (daily)

**Running Containers:**
- `collector_manager` - Using `collector_manager_collector_network` (bridge)

**Connectivity:**
- ⚠️ Container: **LIKELY BROKEN** - Bridge mode + `localhost` won't work
- ✅ Cron script: **WORKING** - Runs natively on host via `python scripts/...`

**Action Required:**
Same solutions as binance_live_data - switch to host networking or update DB_HOST.

---

## Summary of Findings

| Service | Deployment | Network Mode | DB Config | Status | Action Needed |
|---------|-----------|--------------|-----------|--------|---------------|
| **yfin_data_collect** | Native (cron) | N/A | localhost:55432 | ✅ Working | None |
| **igTrade_api cron** | Native (cron) | N/A | localhost:55432 | ✅ Working | None |
| **ig-stream container** | Docker | **host** | localhost:55432 | ✅ Fixed | None |
| **binance_collector container** | Docker | **bridge** | localhost:55432 | ⚠️ Broken | Fix needed |
| **binance cron** | Native (cron) | N/A | localhost:55432 | ✅ Working | None |
| **collector_manager container** | Docker | **bridge** | localhost:55432 | ⚠️ Broken | Fix needed |
| **collector_manager cron** | Native (cron) | N/A | localhost:55432 | ✅ Working | None |

---

## Root Cause Analysis

### Why Bridge Networking Breaks with localhost

When a Docker container uses bridge networking:
1. Container gets its own network namespace
2. "localhost" inside container = container's loopback (127.0.0.1)
3. "localhost" does NOT reach the host's loopback
4. PostgreSQL on host's 127.0.0.1:5432 is unreachable
5. PostgreSQL on host's 0.0.0.0:55432 IS reachable (but not via "localhost")

### Why Host Networking Works

With `network_mode: host`:
1. Container shares host's network namespace
2. "localhost" inside container = host's loopback
3. Can reach host's 127.0.0.1 and 0.0.0.0 services

### Why Cron Scripts Work

Cron scripts run natively on host:
- Execute directly on host (not in containers)
- Can use `localhost` to reach host services
- No Docker networking layer involved

---

## Testing Recommendations

### Test 1: Verify Container Database Access
```bash
# From inside a bridge-mode container
docker exec -it binance_collector ash
nc -zv localhost 55432  # Should FAIL
nc -zv 172.17.0.1 55432  # Should SUCCEED (if using bridge gateway)
```

### Test 2: Verify Cron Script Access
```bash
# Run cron script manually (on host)
cd /home/farq/projects/binance_live_data
./venv/bin/python scripts/upload_to_postgres.py --dry-run
# Should work - native host process
```

### Test 3: Check Container Logs for Connection Errors
```bash
docker logs binance_collector --tail 50 | grep -i "connection\|error\|postgres"
docker logs collector_manager --tail 50 | grep -i "connection\|error\|postgres"
```

---

## Recommended Next Steps

1. **Immediate:** Check logs of `binance_collector` and `collector_manager` containers for database connection errors

2. **Short-term:** Apply fixes to both services:
   - **Preferred:** Switch to `network_mode: host` (consistent with igTrade_api)
   - **Alternative:** Update `DB_HOST` to use bridge gateway or host IP

3. **Documentation:** Update `.env.example` files with notes about Docker networking

4. **Long-term Consideration:** Since PostgreSQL 55432 is already on `0.0.0.0`, consider whether:
   - All containers should standardize on host networking for database access
   - OR use a consistent pattern with bridge networking + explicit host IPs

---

## Files to Review/Update

### binance_live_data
- `docker-compose.yml` - Network configuration
- `.env` - DB_HOST configuration
- `.env.example` - Documentation
- `scripts/upload_to_postgres.py` - Connection logic

### collector_manager
- `docker-compose.yml` - Network configuration
- `.env` - DB_HOST configuration
- `.env.example` - Documentation (if exists)
- `scripts/load_transformed_data_lake.py` - Connection logic
- `scripts/create_transformed_datasets.py` - Check if uses DB

---

## Additional Context

**Security Hardening Changes:**
- PostgreSQL port 5432 restricted to 127.0.0.1 only
- PostgreSQL port 55432 exposed on 0.0.0.0
- Intent: Limit access to secure port, allow broader access to hardened port

**Why This Matters:**
- Bridge-mode containers trying to reach "localhost" will fail
- Host-mode containers and native cron scripts continue working
- This is a network addressing issue, not a firewall/permissions issue

---

## Questions for Review

1. Are the `binance_collector` and `collector_manager` containers currently experiencing database connection errors?

2. Is there a preference for host networking vs bridge networking for database-dependent containers?

3. Should we implement a standardized approach across all services?

4. Are there any other services or containers not listed here that might access PostgreSQL?

5. Should operational runbooks be updated to reflect these networking requirements?
