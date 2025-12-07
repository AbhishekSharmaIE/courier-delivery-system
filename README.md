# Courier Delivery System

A full-stack courier delivery management system built with Flask, PostgreSQL, and AWS services.

## 🚀 Features

- Package creation and tracking
- Real-time status updates
- Address geocoding (Ireland/EIRCODE support)
- Distance calculation and pricing
- Email notifications (AWS SES)
- SNS notifications
- File uploads to S3
- Full CRUD operations
- Modern web UI

## 🏗️ Architecture

- **Backend**: Flask (Python)
- **Database**: PostgreSQL (AWS RDS)
- **Storage**: AWS S3
- **Notifications**: AWS SNS & SES
- **Hosting**: AWS EC2
- **Frontend**: HTML/CSS/JavaScript

## 📋 Prerequisites

- Python 3.10+
- AWS Account
- PostgreSQL database (RDS or local)

## 🔧 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "AWS delivery project"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize database:
```bash
python3 -c "from db_config import init_db; init_db()"
```

5. Run the application:
```bash
python3 app.py
```

## 🌐 Access

- **Local**: http://localhost:5000
- **EC2**: http://ec2-3-80-70-128.compute-1.amazonaws.com:5000
- **GitHub Pages**: [View on GitHub Pages](https://your-username.github.io/repo-name/)

## 📁 Project Structure

```
.
├── app.py                 # Main Flask application
├── db_config.py           # Database configuration
├── aws_services.py         # AWS integrations
├── delivery_optimizer.py   # Distance & pricing calculations
├── geocoder.py            # Address geocoding
├── requirements.txt       # Python dependencies
├── static/                # Frontend files
│   └── index.html         # Main UI
└── .github/
    └── workflows/         # CI/CD pipelines
```

## 🔐 Environment Variables

Required environment variables (see `.env.example`):

```bash
DB_TYPE=postgres
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password

AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET=your-bucket
SNS_TOPIC_ARN=your-topic-arn
SES_FROM_EMAIL=your-email@example.com
```

## 🧪 Testing

```bash
# Run tests
pytest

# Test health endpoint
curl http://localhost:5000/api/health
```

## 📚 API Endpoints

- `GET /api/health` - Health check
- `POST /api/packages` - Create package
- `GET /api/packages` - List packages
- `GET /api/packages/<id>` - Get package details
- `PUT /api/packages/<id>` - Update package
- `DELETE /api/packages/<id>` - Delete package
- `GET /api/packages/track/<tracking_id>` - Track package
- `PUT /api/packages/<id>/status` - Update status

## 🔄 CI/CD

This project includes:
- **CodeQL**: Security analysis
- **Build & Test**: Automated testing
- **Test Deployment**: Deployment pipeline
- **GitHub Pages**: Static site deployment

Workflows are located in `.github/workflows/`

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Status**: ✅ Production Ready
**Last Updated**: December 2025
