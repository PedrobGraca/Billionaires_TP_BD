import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from flask import abort, render_template, Flask
import logging
import db

APP = Flask(__name__)

# 10 different SQL queries
QUERIES = {
    1: {
        'question': '1) Portuguese billionaires and their sources of wealth',
        'sql': '''
            SELECT full_name, position, wealth, industry, group_concat(source, ', ') as sources
            FROM billionaires
            JOIN countries ON c_id = country_of_citizenship
            NATURAL JOIN sources
            WHERE country_name LIKE 'Portugal'
            GROUP BY b_id
        '''
    },
    2: {
        'question': '2) Wealth stats by gender for "Technology" industry',
        'sql': '''
            SELECT gender, count(*) as total, avg(wealth) as avg_wealth
            FROM billionaires
            WHERE industry = 'Technology'
            GROUP BY gender
            ORDER BY total DESC
        '''
    },
    3: {
        'question': '3) Billionaires listed as families (containing "&")',
        'sql': '''
            SELECT full_name, wealth, last_name, first_name
            FROM billionaires
            WHERE full_name LIKE '%&%'
            ORDER BY position
        '''
    },
    4: {
        'question': '4) Industries with >100 billionaires and >1T total wealth',
        'sql': '''
            SELECT industry, count(*) as num, sum(wealth) as total
            FROM billionaires
            GROUP BY industry
            HAVING num > 100 AND total > 1000000
        '''
    },
    5: {
        'question': '5) Billionaires living outside their country of citizenship',
        'sql': '''
            SELECT full_name, gender, cr.country_name as residence, cc.country_name as citizenship
            FROM billionaires
            JOIN countries cr ON cr.c_id = country_of_residence
            JOIN countries cc ON cc.c_id = country_of_citizenship
            WHERE country_of_residence != country_of_citizenship
            ORDER BY gender, cr.c_id
        '''
    },
    6: {
        'question': '6) Countries with >10 billionaires and Life Expectancy >80',
        'sql': '''
            SELECT country_name, count(b_id) as n_billionaires, sum(wealth) total_wealth, life_expectancy
            FROM billionaires 
            JOIN countries ON c_id = country_of_residence
            GROUP BY c_id
            HAVING n_billionaires > 10 AND life_expectancy > 80
            ORDER BY n_billionaires DESC
        '''
    },
    7: {
        'question': '7) Wealth stats by US residence region',
        'sql': '''
            SELECT residence_region, count(*) as n_billionaires, sum(wealth) as total_wealth, avg(wealth) as avg_wealth
            FROM billionaires
            WHERE residence_region IS NOT NULL
            GROUP BY residence_region
            ORDER BY total_wealth DESC
        '''
    },
    8: {
        'question': '8) Countries with no resident billionaires',
        'sql': '''
            SELECT country_name
            FROM countries c
            LEFT JOIN billionaires ON country_of_residence = c_id
            WHERE b_id IS NULL
            ORDER BY country_name
        '''
    },
    9: {
        'question': '9) Countries (>5 billionaires) with highest average billionaire wealth',
        'sql': '''
            SELECT country_name, avg(wealth) as avg_wealth, cpi
            FROM billionaires
            JOIN countries ON c_id = country_of_residence
            GROUP BY country_name
            HAVING count(b_id) > 5 AND cpi IS NOT NULL
            ORDER BY avg_wealth DESC
        '''
    },
    10: {
        'question': '10) Birth decades and most common industries',
        'sql': '''
            SELECT decade_birth, industry, n_billionaires
            FROM (
                SELECT 
                  (cast(birth_year as integer) / 10) * 10 as decade_birth,
                  industry,
                  count(*) n_billionaires
                FROM billionaires
                WHERE birth_year is not null
                GROUP BY decade_birth, industry
            )
            GROUP BY decade_birth
            HAVING n_billionaires = max(n_billionaires)
            ORDER BY decade_birth desc;
        '''
    }
}

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
    # List top 10 billionaires by wealth
    top10 = db.execute('''
    SELECT b_id, position, wealth, full_name, industry, c_id, country_name
    FROM BILLIONAIRES JOIN COUNTRIES ON (country_of_citizenship=c_id)
    LIMIT 10
                       ''')
    logging.info(stats)
    return render_template('index.html', stats=stats, top10=top10)

# Billionaires List
@APP.route('/billionaires/')
def list_billionaires():
    billionaires = db.execute('''
      SELECT b_id, full_name, wealth, industry, position
      FROM BILLIONAIRES
      ORDER BY position
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

# Queries page
@APP.route('/queries/')
def queries_list():
    return render_template('queries.html', queries=QUERIES)

# General function for the 10 queries
@APP.route('/queries/<int:id>/')
def execute_query(id):
    if id not in QUERIES:
        abort(404, 'Query not found')
    
    query_data = QUERIES[id]
    cursor = db.execute(query_data['sql'])
    rows = cursor.fetchall()
    
    # Extract column names from cursor description for the generic template
    if cursor.description:
        headers = [desc[0] for desc in cursor.description]
    else:
        headers = []

    return render_template('query-result.html', 
                           title=query_data['question'], 
                           headers=headers, 
                           rows=rows)