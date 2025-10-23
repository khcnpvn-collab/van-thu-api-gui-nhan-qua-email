# Hướng dẫn Deploy Email Processor API

## 🐳 Deploy với Docker

### Yêu cầu

- Docker >= 20.10
- Docker Compose >= 1.29
- Đã có file `.env` và `email_format.txt`

### Bước 1: Build Docker Image

```bash
# Cách 1: Dùng script tự động
chmod +x docker-build.sh
./docker-build.sh

# Cách 2: Build thủ công
docker build -t email-processor:latest .
```

### Bước 2: Chạy Container

**Cách 1: Dùng Docker Compose (Khuyến nghị)**

```bash
# Dùng script tự động
chmod +x docker-run.sh
./docker-run.sh

# Hoặc chạy thủ công
docker-compose up -d
```

**Cách 2: Chạy trực tiếp với Docker**

```bash
docker run -d \
  --name email-processor-api \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/email_format.txt:/app/email_format.txt:ro \
  --restart unless-stopped \
  email-processor:latest
```

### Bước 3: Kiểm tra Container

```bash
# Xem logs
docker-compose logs -f

# Xem status
docker-compose ps

# Test API
curl http://localhost:8000/
```

## 📦 Deploy lên VM/Server

### Option 1: Docker Compose trên VM

1. **Chuẩn bị VM**
```bash
# SSH vào VM
ssh user@your-vm-ip

# Cài Docker và Docker Compose
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

2. **Upload code lên VM**
```bash
# Từ máy local
scp -r /path/to/email-processor user@your-vm-ip:/home/user/

# Hoặc dùng git
ssh user@your-vm-ip
git clone <your-repo-url>
cd email-processor
```

3. **Chạy trên VM**
```bash
# Build và start
./docker-run.sh

# Hoặc
docker-compose up -d --build
```

4. **Setup Firewall**
```bash
# Mở port 8000
sudo ufw allow 8000/tcp
sudo ufw reload
```

### Option 2: Export/Import Docker Image

1. **Export image từ máy local**
```bash
# Build image
docker build -t email-processor:latest .

# Save thành file .tar
docker save email-processor:latest -o email-processor.tar

# Compress để giảm kích thước
gzip email-processor.tar
```

2. **Upload lên VM**
```bash
scp email-processor.tar.gz user@your-vm-ip:/home/user/
```

3. **Load và chạy trên VM**
```bash
# SSH vào VM
ssh user@your-vm-ip

# Uncompress và load image
gunzip email-processor.tar.gz
docker load -i email-processor.tar

# Chạy container
docker run -d \
  --name email-processor-api \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/email_format.txt:/app/email_format.txt:ro \
  --restart unless-stopped \
  email-processor:latest
```

## 🔧 Quản lý Container

### Xem logs
```bash
docker-compose logs -f email-processor
```

### Restart container
```bash
docker-compose restart
```

### Stop container
```bash
docker-compose down
```

### Update code và redeploy
```bash
# Pull code mới
git pull

# Rebuild và restart
docker-compose up -d --build
```

### Xóa container và image
```bash
docker-compose down
docker rmi email-processor:latest
```

## 📊 Monitoring

### Xem resource usage
```bash
docker stats email-processor-api
```

### Health check
```bash
curl http://localhost:8000/
```

### Xem container details
```bash
docker inspect email-processor-api
```

## 🔐 Security Best Practices

1. **Không commit credentials**
   - File `.env` đã được gitignore, tuyệt đối không commit
   - Sử dụng Docker secrets hoặc env variables trong production

2. **Chạy với non-root user**
   - Thêm vào Dockerfile:
   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```

3. **Sử dụng HTTPS**
   - Setup nginx reverse proxy với SSL
   - Hoặc dùng Traefik với Let's Encrypt

4. **Limit resources**
   ```yaml
   # Trong docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '0.5'
         memory: 512M
   ```

## 🌐 Setup với Nginx (Optional)

1. **Cài Nginx trên VM**
```bash
sudo apt-get install nginx
```

2. **Config Nginx reverse proxy**
```nginx
# /etc/nginx/sites-available/email-processor
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. **Enable và restart Nginx**
```bash
sudo ln -s /etc/nginx/sites-available/email-processor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔄 Auto-restart với systemd (Alternative)

Nếu không dùng Docker restart policy:

```bash
# Tạo service file
sudo nano /etc/systemd/system/email-processor.service
```

```ini
[Unit]
Description=Email Processor API Container
Requires=docker.service
After=docker.service

[Service]
Restart=always
ExecStart=/usr/bin/docker-compose -f /path/to/email-processor/docker-compose.yml up
ExecStop=/usr/bin/docker-compose -f /path/to/email-processor/docker-compose.yml down

[Install]
WantedBy=multi-user.target
```

```bash
# Enable và start
sudo systemctl daemon-reload
sudo systemctl enable email-processor
sudo systemctl start email-processor
```

## 📝 Troubleshooting

### Container không start
```bash
# Xem logs chi tiết
docker-compose logs

# Xem docker daemon logs
sudo journalctl -u docker
```

### Port 8000 đã bị chiếm
```bash
# Tìm process đang chiếm port
sudo lsof -i :8000

# Hoặc đổi port trong docker-compose.yml
ports:
  - "8080:8000"
```

### Container chạy nhưng API không trả lời
```bash
# Vào trong container để debug
docker exec -it email-processor-api bash
python -c "import requests; print(requests.get('http://localhost:8000/').json())"
```

## ✅ Checklist Deploy

- [ ] Docker và Docker Compose đã cài
- [ ] File `.env` đã chuẩn bị (copy từ `.env.example`)
- [ ] File `email_format.txt` đã có
- [ ] Build image thành công
- [ ] Container start được
- [ ] Health check pass
- [ ] API trả về response đúng
- [ ] Firewall đã mở port
- [ ] Setup monitoring/logging
- [ ] Backup credentials

## 🎯 Quick Commands

```bash
# Build
./docker-build.sh

# Run
./docker-run.sh

# Logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart

# Clean up
docker-compose down && docker system prune -a
```

