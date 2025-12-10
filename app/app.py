import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from flask import render_template, Flask
import logging
import db

APP = Flask(__name__)

# Start page
@APP.route('/')
def index():
    stats = {}
    # Count total billionaires and countries
    stats = db.execute('''
    SELECT * FROM
      (SELECT COUNT(*) n_billionaires FROM BILLIONAIRES)
    JOIN
      (SELECT COUNT(*) n_countries FROM COUNTRIES)
    ''').fetchone()
    logging.info(stats)
    return render_template('index.html', stats=stats)

# Billionaires List
@APP.route('/billionaires/')
def list_billionaires():
    billionaires = db.execute('''
      SELECT b_id, full_name, wealth, industry, position
      FROM BILLIONAIRES
      ORDER BY position ASC
    ''').fetchall()
    return render_template('billionaire-list.html', billionaires=billionaires)

# Billionaire Details
@APP.route('/billionaires/<int:id>/')
def get_billionaire(id):
    # Fetch billionaire details and join with Countries to get names
    billionaire = db.execute('''
      SELECT B.*, 
             C1.country_name AS citizenship_country, 
             C2.country_name AS residence_country
      FROM BILLIONAIRES B
      LEFT JOIN COUNTRIES C1 ON B.country_of_citizenship = C1.c_id
      LEFT JOIN COUNTRIES C2 ON B.country_of_residence = C2.c_id
      WHERE b_id = ?
    ''', [id]).fetchone()

    if billionaire is None:
        abort(404, 'Billionaire id {} does not exist.'.format(id))

    # Fetch sources of wealth
    sources = db.execute('''
      SELECT source 
      FROM SOURCES 
      WHERE b_id = ?
    ''', [id]).fetchall()

    return render_template('billionaire.html', 
                           billionaire=billionaire, sources=sources)

# Search Billionaires
@APP.route('/billionaires/search/<expr>/')
def search_billionaire(expr):
  search = { 'expr': expr }
  expr = '%' + expr + '%'
  billionaires = db.execute(''' 
      SELECT b_id, full_name, wealth, industry, position
      FROM BILLIONAIRES 
      WHERE full_name LIKE ?
      ORDER BY wealth DESC
      ''', [expr]).fetchall()
  return render_template('billionaire-search.html',
           search=search, billionaires=billionaires)

# Countries List
@APP.route('/countries/')
def list_countries():
    countries = db.execute('''
      SELECT c_id, country_name, pop, gdp 
      FROM COUNTRIES
      ORDER BY country_name
    ''').fetchall()
    return render_template('country-list.html', countries=countries)

# Country Details
@APP.route('/countries/<int:id>/')
def get_country(id):
  country = db.execute('''
    SELECT *
    FROM COUNTRIES 
    WHERE c_id = ?
    ''', [id]).fetchone()

  if country is None:
     abort(404, 'Country id {} does not exist.'.format(id))

  # List billionaires who are citizens of this country
  citizens = db.execute('''
    SELECT b_id, full_name, wealth, position
    FROM BILLIONAIRES
    WHERE country_of_citizenship = ?
    ORDER BY wealth DESC
    ''', [id]).fetchall()

  return render_template('country.html', 
           country=country, citizens=citizens)

# Industries List
@APP.route('/industries/')
def list_industries():
    # Distinct industries from the Billionaires table
    industries = db.execute('''
      SELECT DISTINCT industry 
      FROM BILLIONAIRES
      ORDER BY industry
    ''').fetchall()
    return render_template('industry-list.html', industries=industries)

# Industry Details
@APP.route('/industries/<string:name>/')
def view_industry(name):
  billionaires = db.execute('''
    SELECT b_id, full_name, wealth, position
    FROM BILLIONAIRES 
    WHERE industry = ?
    ORDER BY wealth DESC
    ''', [name]).fetchall()

  return render_template('industry.html', 
           industry=name, billionaires=billionaires)
