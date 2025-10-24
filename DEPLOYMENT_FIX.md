# 🚀 Fix Container Timeout - Deployment Guide

## 📋 TÓM TẮT VẤN ĐỀ

**Lỗi gặp phải:**
```
Connection timed out (os error 110)
error sending request for url (http://62.72.57.70:8000/sendDocumentOutgoing)
```

**Nguyên nhân:** Container bị stop/crash sau một thời gian do:
- Healthcheck không đúng
- Thiếu resource limits
- Không có proper restart policy
- Uvicorn config chưa tối ưu

---

## ✅ NHỮNG GÌ ĐÃ ĐƯỢC FIX

### 1. **Dockerfile**
```diff
+ # Cài curl cho healthcheck reliable
+ RUN apt-get install -y curl

+ # Healthcheck với start-period dài hơn
+ HEALTHCHECK --start-period=30s --retries=3

+ # Uvicorn với 2 workers và keep-alive timeout
+ CMD ["uvicorn", "main:app", "--workers", "2", "--timeout-keep-alive", "65"]
```

**Lợi ích:**
- ✅ Healthcheck không fail khi app đang khởi động
- ✅ 2 workers xử lý concurrent requests
- ✅ Keep-alive 65s tương thích với most proxies

### 2. **docker-compose.yml**
```diff
- restart: unless-stopped
+ restart: always

+ # Resource limits
+ deploy:
+   resources:
+     limits:
+       memory: 1G
+       cpus: '1.0'

+ # Healthcheck tốt hơn
+ healthcheck:
+   retries: 5
+   start_period: 40s

+ # Log rotation tự động
+ logging:
+   options:
+     max-size: "10m"
+     max-file: "3"
```

**Lợi ích:**
- ✅ Container tự restart khi crash
- ✅ Giới hạn memory để tránh OOM kill
- ✅ Logs không làm đầy disk
- ✅ Healthcheck ít false positive hơn

### 3. **Token Caching**
```python
# Trước: Request token mỗi lần
# Sau: Cache token 5 phút, reuse cho tất cả calls
```

**Lợi ích:**
- ✅ Giảm authentication requests từ 11 → 1
- ✅ API nhanh hơn
- ✅ Tránh rate limit

### 4. **Monitoring Script**
- Script `check_container_health.sh` tự động kiểm tra và restart nếu cần
- Có thể chạy với cron mỗi 5 phút

---

## 🚀 DEPLOYMENT STEPS

### Bước 1: SSH vào server

```bash
ssh user@62.72.57.70
cd /path/to/project
```

### Bước 2: Pull code mới

```bash
git pull origin main
```

### Bước 3: Rebuild container

```bash
# Stop container cũ
docker-compose down

# Rebuild với code mới
docker-compose up -d --build

# Xem logs để check
docker-compose logs -f
```

### Bước 4: Verify deployment

```bash
# 1. Check container running
docker ps | grep email-processor

# 2. Test API từ server
curl http://localhost:8000/

# 3. Test từ bên ngoài
curl http://62.72.57.70:8000/

# 4. Check healthcheck status
docker inspect email-processor-api | grep -A 10 Health
```

### Bước 5: Setup monitoring (Optional but recommended)

```bash
# Cấp quyền cho script
chmod +x check_container_health.sh

# Test script
./check_container_health.sh

# Setup cron job (check mỗi 5 phút)
crontab -e

# Thêm dòng này:
*/5 * * * * cd /path/to/project && ./check_container_health.sh
```

---

## 🔍 MONITORING & DEBUGGING

### Xem logs realtime
```bash
docker-compose logs -f
```

### Xem resource usage
```bash
docker stats email-processor-api
```

### Xem container status
```bash
docker ps -a | grep email-processor
```

### Test API health
```bash
# Từ server
curl http://localhost:8000/

# Từ bên ngoài
curl http://62.72.57.70:8000/

# Test send email API
curl -X POST "http://62.72.57.70:8000/sendDocumentOutgoing" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: multipart/form-data" \
  -F 'data={"mailTo":"test@example.com","subject":"Test",...}'
```

---

## ⚙️ CONFIGURATION TUNING

### Nếu vẫn gặp timeout sau khi deploy:

#### 1. Tăng workers (nếu CPU > 2 cores)
```bash
# Edit Dockerfile
CMD ["uvicorn", "main:app", "--workers", "4", ...]
```

#### 2. Tăng memory limit (nếu có nhiều RAM)
```yaml
# Edit docker-compose.yml
limits:
  memory: 2G
```

#### 3. Tăng healthcheck timeout
```yaml
# Edit docker-compose.yml
healthcheck:
  timeout: 20s
  start_period: 60s
```

#### 4. Check firewall
```bash
# Mở port 8000
sudo ufw allow 8000/tcp
sudo ufw status

# Hoặc cho IP cụ thể
sudo ufw allow from SUPABASE_IP to any port 8000
```

---

## 🐛 COMMON ISSUES AFTER DEPLOYMENT

### Issue 1: Container không start
```bash
# Check logs
docker logs email-processor-api --tail 100

# Thường do:
# - Missing .env file
# - Invalid env variables
# - Port conflict

# Fix:
docker-compose down
docker-compose up -d --build
```

### Issue 2: Healthcheck failed
```bash
# Check healthcheck
docker exec email-processor-api curl http://localhost:8000/

# Nếu fail, check:
# - App có đang chạy không
# - Port 8000 có đúng không
# - Curl đã cài chưa

# Debug:
docker exec -it email-processor-api bash
curl http://localhost:8000/
```

### Issue 3: Vẫn bị timeout từ Supabase
```bash
# 1. Test từ server
curl -v http://localhost:8000/

# 2. Test từ external
curl -v http://62.72.57.70:8000/

# 3. Check firewall
sudo ufw status
sudo iptables -L

# 4. Check if port listening
sudo netstat -tlnp | grep 8000

# 5. Test với telnet
telnet 62.72.57.70 8000
```

### Issue 4: High memory usage
```bash
# Check usage
docker stats email-processor-api

# Nếu > 80%, tăng limit hoặc giảm workers
# Edit docker-compose.yml
```

---

## 📊 EXPECTED RESULTS

### Sau khi deploy thành công:

✅ **Container Status:**
```bash
$ docker ps
CONTAINER ID   NAME                  STATUS                    PORTS
abc123         email-processor-api   Up 5 minutes (healthy)    0.0.0.0:8000->8000/tcp
```

✅ **Health Check:**
```bash
$ curl http://localhost:8000/
{"status":"running","message":"Email Processor API đang hoạt động","version":"1.0.0"}
```

✅ **Resource Usage:**
```
CPU: < 50%
Memory: < 500MB
Restart Count: 0
```

✅ **Logs (no errors):**
```
INFO:     Started server process [1]
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Token mới - valid trong 5 phút
```

✅ **From Supabase:**
```javascript
// No more timeout errors
const response = await fetch('http://62.72.57.70:8000/sendDocumentOutgoing', {...});
// Success!
```

---

## 🎯 PERFORMANCE EXPECTATIONS

| Metric | Before Fix | After Fix |
|--------|-----------|-----------|
| Auth requests (5 emails) | 11 | 1 |
| Uptime | ~hours | days/weeks |
| Response time | 2-5s | 0.5-2s |
| Timeout errors | frequent | rare |
| Container restarts | frequent | none |

---

## 🆘 ROLLBACK PLAN

Nếu deployment gặp vấn đề nghiêm trọng:

```bash
# 1. Quay lại version cũ
git checkout <previous-commit-hash>

# 2. Rebuild
docker-compose down
docker-compose up -d --build

# 3. Hoặc dùng backup image
docker load < email-processor-backup.tar.gz
docker-compose up -d
```

---

## 📞 SUPPORT CHECKLIST

Nếu vẫn gặp vấn đề, collect thông tin sau:

```bash
# 1. Container logs
docker logs email-processor-api --tail 200 > logs.txt

# 2. Resource stats
docker stats email-processor-api --no-stream > stats.txt

# 3. Healthcheck status
docker inspect email-processor-api | grep -A 20 Health > health.txt

# 4. Environment check
docker exec email-processor-api env > env.txt

# 5. Network check
curl -v http://localhost:8000/ > curl-local.txt
curl -v http://62.72.57.70:8000/ > curl-external.txt
```

---

## 📝 POST-DEPLOYMENT CHECKLIST

- [ ] Container đang chạy (`docker ps`)
- [ ] Healthcheck passing
- [ ] API responds từ localhost
- [ ] API responds từ external IP
- [ ] Test send email API works
- [ ] Test receive email API works
- [ ] Supabase Edge Function không còn timeout
- [ ] Logs không có errors
- [ ] Memory usage < 80%
- [ ] Setup monitoring (cron job)
- [ ] Backup image & config

---

## 🎉 KẾT LUẬN

Với các fixes này, container sẽ:
- ✅ **Stable**: Tự động restart khi crash
- ✅ **Reliable**: Healthcheck đúng, không false positive
- ✅ **Fast**: Token caching, multiple workers
- ✅ **Safe**: Resource limits, không OOM
- ✅ **Maintainable**: Logs rotation, monitoring script

**Deployment thành công → No more timeout! 🎊**

