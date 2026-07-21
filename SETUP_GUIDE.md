# EduPath AI Platform - Setup and Running Guide

## Prerequisites

### System Requirements
- Python 3.8 or higher
- MySQL Server 5.7 or higher
- Git (optional, for version control)
- 4GB+ RAM recommended
- 2GB+ disk space

### Software Dependencies
- Python package manager (pip)
- MySQL Workbench or command line client
- Code editor (VS Code, PyCharm, etc.)

## Step 1: Environment Setup

### 1.1 Clone or Download the Project
```bash
# If using Git
git clone <repository-url>
cd EduPath_Updated

# Or download and extract the ZIP file
```

### 1.2 Create Virtual Environment
```bash
# Create virtual environment
python -m venv edupath_env

# Activate virtual environment
# Windows:
edupath_env\Scripts\activate

# macOS/Linux:
source edupath_env/bin/activate
```

### 1.3 Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

## Step 2: Database Setup

### 2.1 Install MySQL Server
**Windows:**
1. Download MySQL Installer from https://dev.mysql.com/downloads/installer/
2. Run installer and select "Server only"
3. Set root password (remember it for later)
4. Configure MySQL to start automatically

**macOS:**
```bash
# Using Homebrew
brew install mysql
brew services start mysql
mysql_secure_installation
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

### 2.2 Create Database
```sql
# Log in to MySQL
mysql -u root -p

# Create database
CREATE DATABASE edupath_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Create user (optional, for better security)
CREATE USER 'edupath_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON edupath_db.* TO 'edupath_user'@'localhost';
FLUSH PRIVILEGES;

EXIT;
```

### 2.3 Configure Database Connection
Create a `.env` file in the project root:

```bash
# Copy the template
cp .env.example .env
```

Edit the `.env` file with your database credentials:

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost/edupath_db

# Or if you created a dedicated user:
DATABASE_URL=mysql+pymysql://edupath_user:your_password@localhost/edupath_db

# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-this-in-production

# HuggingFace AI (Required for AI functionality)
HF_API_KEY=your-huggingface-api-key-here
```

## Step 3: HuggingFace API Setup

### 3.1 Get HuggingFace API Key
1. Visit https://huggingface.co/settings/tokens
2. Sign up or log in
3. Navigate to Access Tokens section
4. Create a new token (Read access is sufficient)
5. Copy the key to your `.env` file

### 3.2 Update Environment Variables
In your `.env` file:
```env
HF_API_KEY=hf_your_actual_api_key_here
```

## Step 4: Initialize Database Tables

### 4.1 Run Database Initialization
```bash
# Start Flask shell
python -c "from app import create_app; from database import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database tables created successfully!')"
```

### 4.2 Verify Database Setup
```sql
# Log in to MySQL and check tables
mysql -u root -p edupath_db

SHOW TABLES;
```

You should see tables like:
- users
- assessment_sessions
- assessment_responses
- career_paths
- skills
- etc.

## Step 5: Run the Application

### 5.1 Start the Development Server
```bash
# Make sure virtual environment is activated
python app.py
```

### 5.2 Access the Application
Open your web browser and navigate to:
- **Main Application**: http://127.0.0.1:5000
- **Dashboard**: http://127.0.0.1:5000/dashboard (after login)
- **AI Chat**: http://127.0.0.1:5000/assessment/ai-chat

## Step 6: Test the Application

### 6.1 User Registration
1. Navigate to http://127.0.0.1:5000/auth/register
2. Fill out the registration form
3. Verify you can successfully register

### 6.2 User Login
1. Navigate to http://127.0.0.1:5000/auth/login
2. Login with your registered credentials
3. Verify you're redirected to the dashboard

### 6.3 AI Assessment
1. Navigate to http://127.0.0.1:5000/assessment/ai-chat
2. Start a conversation with the AI assistant
3. Test the assessment functionality

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Error
**Error**: `Can't connect to MySQL server`
**Solution**:
- Verify MySQL server is running
- Check database credentials in `.env` file
- Ensure database name is correct

#### 2. Import Error
**Error**: `ModuleNotFoundError: No module named 'huggingface_hub'`
**Solution**:
```bash
pip install huggingface_hub
```

#### 3. Database Tables Not Found
**Error**: `Table 'users' doesn't exist`
**Solution**:
- Run database initialization (Step 4.1)
- Verify database connection string

#### 4. HuggingFace API Error
**Error**: `Invalid API key`
**Solution**:
- Verify HuggingFace API key in `.env` file
- Check API key is valid and active

#### 5. Port Already in Use
**Error**: `Address already in use`
**Solution**:
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (Windows)
taskkill /PID <process_id> /F

# Or use different port
python app.py --port 5001
```

## Development Tips

### Running in Debug Mode
```bash
# Set debug mode in .env
FLASK_ENV=development

# Or run with debug flag
python app.py --debug
```

### Database Migrations
For future database schema changes:
```bash
# Install Flask-Migrate
pip install Flask-Migrate

# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Add new feature"

# Apply migration
flask db upgrade
```

### Environment Variables
Create different `.env` files for different environments:
- `.env.development` - Development settings
- `.env.production` - Production settings
- `.env.testing` - Testing settings

## Production Deployment

### For Production Use:
1. Set `FLASK_ENV=production` in `.env`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Configure proper database security
4. Set up SSL/HTTPS
5. Configure proper logging
6. Set up monitoring and backup

### Example Production Command:
```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

## Support

### Getting Help:
1. Check the logs for error messages
2. Verify all environment variables are set
3. Ensure all dependencies are installed
4. Test database connection separately
5. Check HuggingFace API key validity

### Log Files:
- Application logs: Console output
- Database logs: MySQL error logs
- System logs: System event viewer (Windows) or `/var/log/` (Linux)

## Next Steps

After successful setup:
1. Explore the AI chat functionality
2. Take an assessment
3. View career recommendations
4. Test the dashboard features
5. Customize the application as needed

Enjoy using the EduPath AI Platform!
