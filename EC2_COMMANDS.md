# EC2 Instance Commands

## Important Note
If you're **already on the EC2 instance** (you see `ubuntu@ip-172-31-16-129`), you don't need SSH. Just run the commands directly!

## Commands to Run ON the EC2 Instance

### View Application Logs (Live)
```bash
sudo journalctl -u courier-delivery -f
```
Press `Ctrl+C` to exit

### View Recent Logs (Last 50 lines)
```bash
sudo journalctl -u courier-delivery -n 50
```

### Check Service Status
```bash
sudo systemctl status courier-delivery
```

### Restart Application
```bash
sudo systemctl restart courier-delivery
```

### Stop Application
```bash
sudo systemctl stop courier-delivery
```

### Start Application
```bash
sudo systemctl start courier-delivery
```

### View Application Directory
```bash
cd /home/ubuntu/courier-delivery
ls -la
```

### Check Environment Variables
```bash
cd /home/ubuntu/courier-delivery
cat .env
```

### Test Application Locally
```bash
curl http://localhost:5000/api/health
```

## Commands to Run FROM Your Local Machine

### SSH into EC2
```bash
cd "/home/kali/Desktop/AWS delivery project"
ssh -i courier-delivery-key.pem ubuntu@3.80.70.128
```

### View Logs Remotely
```bash
cd "/home/kali/Desktop/AWS delivery project"
ssh -i courier-delivery-key.pem ubuntu@3.80.70.128 'sudo journalctl -u courier-delivery -n 50'
```

### Restart Application Remotely
```bash
cd "/home/kali/Desktop/AWS delivery project"
ssh -i courier-delivery-key.pem ubuntu@3.80.70.128 'sudo systemctl restart courier-delivery'
```

### Check Status Remotely
```bash
cd "/home/kali/Desktop/AWS delivery project"
ssh -i courier-delivery-key.pem ubuntu@3.80.70.128 'sudo systemctl status courier-delivery'
```

## Application URLs

- **Public URL**: http://3.80.70.128:5000
- **Local URL** (from EC2): http://localhost:5000

## Troubleshooting

### If service is not running:
```bash
sudo systemctl start courier-delivery
sudo systemctl enable courier-delivery
```

### If you need to check for errors:
```bash
sudo journalctl -u courier-delivery -n 100 | grep -i error
```

### If you need to check database connection:
```bash
cd /home/ubuntu/courier-delivery
source venv/bin/activate
python3 -c "from db_config import get_db_connection; conn = get_db_connection(); print('Connected!'); conn.close()"
```

