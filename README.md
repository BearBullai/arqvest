# Multi-Asset Portfolio Management System

A comprehensive web-based portfolio management system built with Flask that allows users to track and manage their multi-asset investments including stocks, bonds, ETFs, and other securities.

## Features

- **Multi-User Authentication**: Secure login and registration system with user-specific portfolios
- **Registration Notifications**: Admin receives email notifications for new user registrations
- **Fresh Portfolio for New Users**: Each user starts with a clean, empty portfolio
- **Portfolio Management**: Add, edit, and track securities (user-specific)
- **Multi-Asset Support**: Stocks, bonds, ETFs, mutual funds, etc.
- **Performance Tracking**: Real-time gain/loss calculations
- **Transaction History**: Track buy/sell transactions
- **Portfolio Analytics**: Performance analysis and reporting
- **Responsive Design**: Modern, mobile-friendly interface

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with PostgreSQL
- **Authentication**: Flask-Login
- **Email**: Flask-Mail for registration notifications
- **Frontend**: HTML, CSS, JavaScript
- **Charts**: Chart.js for data visualization
- **Deployment**: Render

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Multi_Asset_Portfolio_Management_System
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   export SESSION_SECRET="your-secret-key"
   export DATABASE_URL="sqlite:///portfolio.db"
   export MAIL_USERNAME="your-email@gmail.com"
   export MAIL_PASSWORD="your-app-password"
   export MAIL_DEFAULT_SENDER="your-email@gmail.com"
   export ADMIN_EMAIL="bearbullai01@gmail.com"
   ```

5. **Run database migration (if upgrading from single-user version)**
   ```bash
   python migrate_db.py
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

7. **Access the application**
   Open your browser and go to `http://localhost:5001`

## New User Registration Flow

1. **User Registration**: New users must register with name, email, phone, and password
2. **Admin Notification**: Registration details are automatically sent to the admin email
3. **Fresh Portfolio**: New users start with an empty portfolio
4. **First Login**: Users are guided to add their first security upon login
5. **User-Specific Data**: All portfolio data is isolated per user

## Database Migration

If you're upgrading from the single-user version to the multi-user version:

1. **Backup your database** (important!)
2. **Run the migration script**:
   ```bash
   python migrate_db.py
   ```
3. **The script will**:
   - Add `user_id` columns to Security and PortfolioSnapshot tables
   - Create a default user for existing data
   - Assign existing securities to the default user
   - Provide login credentials for the default user

## Deployment to Render

### Prerequisites
- GitHub account with your code repository
- Render account (free tier available)

### Step-by-Step Deployment

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Multi-user portfolio management system"
   git push origin main
   ```

2. **Sign up/Login to Render**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account

3. **Create a new Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository containing your portfolio management system

4. **Configure the Web Service**
   - **Name**: `multi-asset-portfolio-management` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app`
   - **Plan**: Free

5. **Add Environment Variables**
   - Click on "Environment" tab
   - Add the following variables:
     - `SESSION_SECRET`: Generate a random secret key
     - `PYTHON_VERSION`: `3.11.0`

6. **Create PostgreSQL Database**
   - Go back to Render dashboard
   - Click "New +" → "PostgreSQL"
   - **Name**: `portfolio-db`
   - **Database**: `portfolio`
   - **User**: `portfolio_user`
   - **Plan**: Free

7. **Link Database to Web Service**
   - Go back to your web service
   - In Environment Variables, add:
     - `DATABASE_URL`: Copy the connection string from your PostgreSQL database

8. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### Alternative: Using render.yaml (Blueprints)

If you prefer using the `render.yaml` file included in this repository:

1. **Push your code with render.yaml to GitHub**
2. **In Render dashboard**: Click "New +" → "Blueprint"
3. **Connect your repository**
4. **Render will automatically create both the web service and database**

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SESSION_SECRET` | Secret key for Flask sessions | Yes |
| `DATABASE_URL` | Database connection string | Yes |
| `PYTHON_VERSION` | Python version to use | No (default: 3.11.0) |

## Database Schema

The application uses the following main models:
- **User**: User authentication and profile information
- **Security**: Portfolio securities with pricing and metadata
- **Transaction**: Buy/sell transaction history
- **PortfolioSnapshot**: Historical portfolio values for performance tracking

## API Endpoints

- `/` - Home page
- `/login` - User login
- `/register` - User registration
- `/portfolio` - Portfolio overview
- `/add_security` - Add new security
- `/analysis` - Portfolio analysis
- `/reports` - Generate reports
- `/profile` - User profile management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue in the GitHub repository. 