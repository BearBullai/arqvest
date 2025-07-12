from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app import app, db, mail
from models import Security, Transaction, PortfolioSnapshot, User
from portfolio_manager import PortfolioManager

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.name}!', 'success')
            
            # Check if user has any securities
            user_securities = Security.query.filter_by(user_id=user.id).first()
            if not user_securities:
                flash('Welcome! Please add your first security to get started.', 'info')
                next_page = request.args.get('next')
                if next_page and next_page != url_for('index'):
                    return redirect(next_page)
                else:
                    return redirect(url_for('add_security'))
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long!', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('register.html')
        
        # Create new user
        try:
            user = User(name=name, email=email, phone=phone)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Send registration notification to admin
            try:
                admin_email = app.config.get('ADMIN_EMAIL', 'bearbullai01@gmail.com')
                msg = Message(
                    subject='New User Registration - Arqvest',
                    recipients=[admin_email],
                    body=f"""
New user registration details:

Name: {name}
Email: {email}
Phone: {phone}
Registration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This user has successfully registered for the Multi-Asset Portfolio Management System.
                    """.strip()
                )
                mail.send(msg)
            except Exception as e:
                # Log the error but don't fail registration
                app.logger.error(f"Failed to send admin notification: {str(e)}")
            
            flash('Registration successful! Please login with your credentials.', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html', user=current_user)

@app.route('/')
@login_required
def index():
    """Home page showing portfolio overview"""
    # Get user-specific portfolio data
    user_securities = Security.query.filter_by(user_id=current_user.id).all()
    
    # Calculate portfolio summary for current user
    total_purchase_value = sum(sec.purchase_value for sec in user_securities)
    total_current_value = sum(sec.current_value for sec in user_securities)
    total_gain_loss = total_current_value - total_purchase_value
    total_gain_loss_percentage = (total_gain_loss / total_purchase_value * 100) if total_purchase_value > 0 else 0
    
    # Calculate asset allocation
    asset_allocation = {}
    if total_current_value > 0:
        for security in user_securities:
            asset_class = security.asset_class
            if asset_class in asset_allocation:
                asset_allocation[asset_class] += security.current_value
            else:
                asset_allocation[asset_class] = security.current_value
        
        # Convert to percentages
        for asset_class in asset_allocation:
            asset_allocation[asset_class] = (asset_allocation[asset_class] / total_current_value) * 100
    
    summary = {
        'total_securities': len(user_securities),
        'securities_count': len(user_securities),  # Alias for template compatibility
        'total_purchase_value': total_purchase_value,
        'total_current_value': total_current_value,
        'total_value': total_current_value,  # Alias for template compatibility
        'total_gain_loss': total_gain_loss,
        'total_gain_loss_percentage': total_gain_loss_percentage,
        'total_gain_loss_pct': total_gain_loss_percentage,  # Alias for template compatibility
        'asset_allocation': asset_allocation
    }
    
    # Calculate metrics for current user
    metrics = PortfolioManager.calculate_portfolio_metrics(user_securities)
    risk = PortfolioManager.calculate_risk_metrics(user_securities)
    
    # Record today's snapshot for current user if not already recorded
    PortfolioManager.record_snapshot(current_user.id)
    
    # Get latest securities for current user
    latest_securities = Security.query.filter_by(user_id=current_user.id).order_by(Security.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                           summary=summary, 
                           metrics=metrics, 
                           risk=risk,
                           latest_securities=latest_securities)

@app.route('/portfolio')
@login_required
def portfolio():
    """Page showing detailed portfolio"""
    securities = Security.query.filter_by(user_id=current_user.id).all()
    
    # Calculate summary for current user
    total_purchase_value = sum(sec.purchase_value for sec in securities)
    total_current_value = sum(sec.current_value for sec in securities)
    total_gain_loss = total_current_value - total_purchase_value
    total_gain_loss_percentage = (total_gain_loss / total_purchase_value * 100) if total_purchase_value > 0 else 0
    
    # Calculate asset allocation
    asset_allocation = {}
    if total_current_value > 0:
        for security in securities:
            asset_class = security.asset_class
            if asset_class in asset_allocation:
                asset_allocation[asset_class] += security.current_value
            else:
                asset_allocation[asset_class] = security.current_value
        
        # Convert to percentages
        for asset_class in asset_allocation:
            asset_allocation[asset_class] = (asset_allocation[asset_class] / total_current_value) * 100
    
    summary = {
        'total_securities': len(securities),
        'total_purchase_value': total_purchase_value,
        'total_current_value': total_current_value,
        'total_value': total_current_value,  # Alias for template compatibility
        'total_gain_loss': total_gain_loss,
        'total_gain_loss_percentage': total_gain_loss_percentage,
        'total_gain_loss_pct': total_gain_loss_percentage,  # Alias for template compatibility
        'asset_allocation': asset_allocation
    }
    
    return render_template('portfolio.html', securities=securities, summary=summary)

@app.route('/add_security', methods=['GET', 'POST'])
@login_required
def add_security():
    """Page for adding a new security to the portfolio"""
    if request.method == 'POST':
        try:
            # Get form data
            ticker = request.form.get('ticker').upper()
            name = request.form.get('name')
            asset_class = request.form.get('asset_class')
            purchase_price = float(request.form.get('purchase_price'))
            current_price = float(request.form.get('current_price'))
            quantity = float(request.form.get('quantity'))
            purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d')
            sector = request.form.get('sector')
            country = request.form.get('country')
            currency = request.form.get('currency', 'INR')
            notes = request.form.get('notes')
            
            # Create new security for current user
            security = Security(
                user_id=current_user.id,
                ticker=ticker,
                name=name,
                asset_class=asset_class,
                purchase_price=purchase_price,
                current_price=current_price,
                quantity=quantity,
                purchase_date=purchase_date,
                sector=sector,
                country=country,
                currency=currency,
                notes=notes
            )
            
            db.session.add(security)
            db.session.commit()
            
            # Create transaction record
            transaction = Transaction(
                security_id=security.id,
                transaction_type='buy',
                price=purchase_price,
                quantity=quantity,
                transaction_date=purchase_date
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            # Send email notification to admin
            try:
                admin_email = app.config.get('ADMIN_EMAIL', 'bearbullai01@gmail.com')
                msg = Message(
                    subject=f'New Security Added by {current_user.name} - Arqvest',
                    recipients=[admin_email],
                    body=f"""
A new security has been added to the portfolio.

User: {current_user.name} ({current_user.email})
Security: {ticker} - {name}
Asset Class: {asset_class}
Purchase Price: {purchase_price}
Current Price: {current_price}
Quantity: {quantity}
Purchase Date: {purchase_date.strftime('%Y-%m-%d')}
Sector: {sector}
Country: {country}
Currency: {currency}
Notes: {notes}
Date Added: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """.strip()
                )
                mail.send(msg)
            except Exception as e:
                app.logger.error(f"Failed to send security add notification: {str(e)}")
            
            flash(f"Security {ticker} added successfully!", "success")
            return redirect(url_for('portfolio'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding security: {str(e)}", "danger")
    
    # Asset classes for dropdown
    asset_classes = [
        'Stock', 'ETF', 'Mutual Fund', 'Government Bonds', 'Corporate Bonds', 
        'Municipal Bonds', 'Cash', 'Cryptocurrency', 'Real Estate', 
        'Commodity', 'Options', 'Futures', 'Other'
    ]
    
    return render_template('add_security.html', asset_classes=asset_classes)

@app.route('/edit_security/<int:security_id>', methods=['GET', 'POST'])
@login_required
def edit_security(security_id):
    """Page for editing an existing security"""
    security = Security.query.filter_by(id=security_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            # Update security data
            security.name = request.form.get('name')
            security.asset_class = request.form.get('asset_class')
            security.current_price = float(request.form.get('current_price'))
            security.quantity = float(request.form.get('quantity'))
            security.sector = request.form.get('sector')
            security.country = request.form.get('country')
            security.currency = request.form.get('currency', 'INR')
            security.notes = request.form.get('notes')
            security.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Send email notification to admin
            try:
                admin_email = app.config.get('ADMIN_EMAIL', 'bearbullai01@gmail.com')
                msg = Message(
                    subject=f'Security Edited by {current_user.name} - Arqvest',
                    recipients=[admin_email],
                    body=f"""
A security has been edited in the portfolio.

User: {current_user.name} ({current_user.email})
Security: {security.ticker} - {security.name}
Asset Class: {security.asset_class}
Current Price: {security.current_price}
Quantity: {security.quantity}
Sector: {security.sector}
Country: {security.country}
Currency: {security.currency}
Notes: {security.notes}
Date Edited: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """.strip()
                )
                mail.send(msg)
            except Exception as e:
                app.logger.error(f"Failed to send security edit notification: {str(e)}")
            
            flash(f"Security {security.ticker} updated successfully!", "success")
            return redirect(url_for('portfolio'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating security: {str(e)}", "danger")
    
    # Asset classes for dropdown
    asset_classes = [
        'Stock', 'ETF', 'Mutual Fund', 'Government Bonds', 'Corporate Bonds', 
        'Municipal Bonds', 'Cash', 'Cryptocurrency', 'Real Estate', 
        'Commodity', 'Options', 'Futures', 'Other'
    ]
    
    return render_template('add_security.html', asset_classes=asset_classes, security=security, edit=True)

@app.route('/delete_security/<int:security_id>', methods=['POST'])
@login_required
def delete_security(security_id):
    """Route for deleting a security"""
    security = Security.query.filter_by(id=security_id, user_id=current_user.id).first_or_404()
    
    try:
        # Delete associated transactions first
        Transaction.query.filter_by(security_id=security_id).delete()
        
        # Delete the security
        db.session.delete(security)
        db.session.commit()
        
        flash(f"Security {security.ticker} deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting security: {str(e)}", "danger")
    
    return redirect(url_for('portfolio'))

@app.route('/analysis')
@login_required
def analysis():
    """Page for displaying portfolio analysis"""
    # Get user-specific securities
    user_securities = Security.query.filter_by(user_id=current_user.id).all()
    
    # Calculate summary for current user
    total_purchase_value = sum(sec.purchase_value for sec in user_securities)
    total_current_value = sum(sec.current_value for sec in user_securities)
    total_gain_loss = total_current_value - total_purchase_value
    total_gain_loss_percentage = (total_gain_loss / total_purchase_value * 100) if total_purchase_value > 0 else 0
    
    # Calculate asset allocation
    asset_allocation = {}
    if total_current_value > 0:
        for security in user_securities:
            asset_class = security.asset_class
            if asset_class in asset_allocation:
                asset_allocation[asset_class] += security.current_value
            else:
                asset_allocation[asset_class] = security.current_value
        
        # Convert to percentages
        for asset_class in asset_allocation:
            asset_allocation[asset_class] = (asset_allocation[asset_class] / total_current_value) * 100
    
    # Calculate sector allocation
    sector_allocation = {}
    for security in user_securities:
        sector = security.sector or 'Unknown'
        if sector in sector_allocation:
            sector_allocation[sector] += security.current_value
        else:
            sector_allocation[sector] = security.current_value
    
    summary = {
        'total_securities': len(user_securities),
        'securities_count': len(user_securities),  # Alias for template compatibility
        'total_purchase_value': total_purchase_value,
        'total_current_value': total_current_value,
        'total_value': total_current_value,  # Alias for template compatibility
        'total_gain_loss': total_gain_loss,
        'total_gain_loss_percentage': total_gain_loss_percentage,
        'total_gain_loss_pct': total_gain_loss_percentage,  # Alias for template compatibility
        'asset_allocation': asset_allocation,
        'sector_allocation': sector_allocation
    }
    
    metrics = PortfolioManager.calculate_portfolio_metrics(user_securities)
    risk = PortfolioManager.calculate_risk_metrics(user_securities)
    
    return render_template('analysis.html', summary=summary, metrics=metrics, risk=risk)

@app.route('/reports')
@login_required
def reports():
    """Page for generating and displaying portfolio reports"""
    # Get user-specific securities
    user_securities = Security.query.filter_by(user_id=current_user.id).all()
    
    # Generate report for current user
    report = PortfolioManager.generate_report(user_securities)
    
    return render_template('reports.html', report=report)

@app.route('/api/portfolio_performance')
@login_required
def portfolio_performance():
    """API endpoint for fetching portfolio performance data"""
    days = request.args.get('days', 30, type=int)
    user_securities = Security.query.filter_by(user_id=current_user.id).all()
    performance = PortfolioManager.get_historical_performance(days, user_securities)
    
    return jsonify(performance)

@app.route('/api/asset_allocation')
@login_required
def asset_allocation():
    """API endpoint for fetching asset allocation data"""
    user_securities = Security.query.filter_by(user_id=current_user.id).all()
    
    # Calculate asset allocation for current user
    asset_allocation = {}
    for security in user_securities:
        asset_class = security.asset_class
        if asset_class in asset_allocation:
            asset_allocation[asset_class] += security.current_value
        else:
            asset_allocation[asset_class] = security.current_value
    
    return jsonify({
        'labels': list(asset_allocation.keys()),
        'data': list(asset_allocation.values())
    })

@app.route('/api/sector_allocation')
@login_required
def sector_allocation():
    """API endpoint for fetching sector allocation data"""
    user_securities = Security.query.filter_by(user_id=current_user.id).all()
    
    # Calculate sector allocation for current user
    sector_allocation = {}
    for security in user_securities:
        sector = security.sector or 'Unknown'
        if sector in sector_allocation:
            sector_allocation[sector] += security.current_value
        else:
            sector_allocation[sector] = security.current_value
    
    return jsonify({
        'labels': list(sector_allocation.keys()),
        'data': list(sector_allocation.values())
    })

@app.route('/api/update_prices', methods=['POST'])
@login_required
def update_prices():
    """API endpoint for updating current prices"""
    data = request.json
    
    try:
        for security_update in data:
            security_id = security_update.get('id')
            current_price = security_update.get('current_price')
            
            if security_id and current_price:
                # Ensure user can only update their own securities
                security = Security.query.filter_by(id=security_id, user_id=current_user.id).first()
                if security:
                    security.current_price = float(current_price)
                    security.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'status': 'success'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/send_user_info', methods=['GET', 'POST'])
def send_user_info():
    """Route to send all registered user information to specified email"""
    # Simple authentication - only allow access to specific email
    if not current_user.is_authenticated or current_user.email != 'bearbullai01@gmail.com':
        flash('Access denied. This page is only for administrators.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Get all users from database
            users = User.query.all()
            
            # Check if email is configured
            if not app.config['MAIL_PASSWORD']:
                # If email not configured, just show the data on the page
                flash('Email not configured. Showing user data on page instead.', 'warning')
                return render_template('send_user_info.html', users=users, user_count=len(users), show_data=True)
            
            # Create email content
            subject = "Registered Users Information - Portfolio Management System"
            
            # Create simple HTML table of user information
            html_content = f"""
            <html>
            <head>
                <style>
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 15px; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Registered Users Information</h2>
                        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Phone</th>
                                <th>Registration Date</th>
                                <th>Last Updated</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for user in users:
                html_content += f"""
                            <tr>
                                <td>{user.id}</td>
                                <td>{user.name}</td>
                                <td>{user.email}</td>
                                <td>{user.phone or 'N/A'}</td>
                                <td>{user.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
                                <td>{user.updated_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
                            </tr>
                """
            
            html_content += f"""
                        </tbody>
                    </table>
                    <p><strong>Total Users:</strong> {len(users)}</p>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_content = "Registered Users Information\n\n"
            text_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            text_content += "ID | Name | Email | Phone | Registration Date | Last Updated\n"
            text_content += "-" * 80 + "\n"
            
            for user in users:
                text_content += f"{user.id} | {user.name} | {user.email} | {user.phone or 'N/A'} | {user.created_at.strftime('%Y-%m-%d %H:%M:%S')} | {user.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            text_content += f"\nTotal Users: {len(users)}"
            
            # Create and send email
            msg = Message(
                subject=subject,
                recipients=['bearbullai01@gmail.com'],
                body=text_content,
                html=html_content
            )
            
            mail.send(msg)
            
            flash(f'User information sent successfully to bearbullai01@gmail.com! Total users: {len(users)}', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            error_msg = str(e)
            if "Username and Password not accepted" in error_msg:
                flash('Email authentication failed. Please configure Gmail app password. Showing user data on page instead.', 'warning')
                return render_template('send_user_info.html', users=users, user_count=len(users), show_data=True)
            else:
                flash(f'Error sending user information: {error_msg}', 'danger')
                return redirect(url_for('index'))
    
    # If GET request, show a confirmation page
    user_count = User.query.count()
    return render_template('send_user_info.html', user_count=user_count)

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Custom 500 page"""
    return render_template('500.html'), 500
