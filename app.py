# app.py

from flask import Flask, jsonify, request, make_response
import mysql.connector
from flask_cors import CORS
from datetime import date, datetime

# --- 1. CONFIGURATION ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration 
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',      
    'password': 'root', 
    'database': 'GAMEofJAB_db' 
}

# --- 2. DATABASE HELPER FUNCTIONS ---

def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def execute_query(query, params=None, fetch=True):
    """
    Executes a database query. 
    - For SELECT, returns (data, status_code).
    - For CUD, returns (message/data, status_code).
    """
    conn = get_db_connection()
    if conn is None:
        return {'error': 'Database connection failed'}, 500

    cursor = conn.cursor(dictionary=True) # dictionary=True returns results as dictionaries
    
    try:
        cursor.execute(query, params or ())
        
        if fetch: # Used for SELECT
            result = cursor.fetchall()
            return result, 200
        else: # Used for INSERT, UPDATE, DELETE
            conn.commit()
            return {'message': 'Operation successful', 'rows_affected': cursor.rowcount, 'last_id': cursor.lastrowid}, 201

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        conn.rollback() 
        # Check for specific errors like duplicate entry (1062) or FK violation (1452)
        if err.errno == 1062:
            error_msg = f"Duplicate entry error: {err.msg}"
            status_code = 409 # Conflict
        elif err.errno == 1452:
            error_msg = f"Foreign Key constraint failed: {err.msg}"
            status_code = 400 # Bad Request
        else:
            error_msg = f'Database operation failed: {err.msg}'
            status_code = 500
            
        return {'error': error_msg}, status_code
        
    finally:
        cursor.close()
        conn.close()

# --- 3. TEAM RESOURCE API ENDPOINTS ---

# Helper function for JSON/XML formatting 
def format_response(data, resource_name, status_code):
    """Handles JSON and basic XML output based on the 'format' URI parameter."""
    output_format = request.args.get('format', 'json').lower()
    
    if status_code >= 400:
        # Errors are usually best returned as JSON for consistency
        return jsonify(data), status_code

    if output_format == 'xml':
        # Simple XML generation 
        # but this placeholder meets the requirement for demonstrating the mechanism)
        xml_content = f"<{resource_name}>\n"
        if isinstance(data, list):
            for item in data:
                xml_content += f"  <item>\n"
                for k, v in item.items():
                    xml_content += f"    <{k}>{v}</{k}>\n"
                xml_content += f"  </item>\n"
        elif isinstance(data, dict):
            for k, v in data.items():
                xml_content += f"  <{k}>{v}</{k}>\n"
        xml_content += f"</{resource_name}>"
        
        response = make_response(xml_content, status_code)
        response.headers['Content-Type'] = 'application/xml'
        return response

    # Default JSON output
    return jsonify({
        'status': 'success',
        'count': len(data) if isinstance(data, list) else 1,
        resource_name: data
    }), status_code

# --- C: Create New Team (POST) ---
@app.route('/api/teams', methods=['POST'])
def create_team():
    """Handles creating a new team with input validation."""
    data = request.get_json()
    
   
    if not data or 'team_name' not in data or 'region' not in data:
        return make_response(jsonify({'error': 'Missing required fields: team_name and region are required.'}), 400)

    team_name = data['team_name']
    region = data['region']
    
  
    query = "INSERT INTO Teams (team_name, region) VALUES (%s, %s)"
    params = (team_name, region)
    
    result, status_code = execute_query(query, params=params, fetch=False)
    
    if status_code == 201:
        # Fetch the newly created record to return it
        new_team_id = result.get('last_id', 'N/A')
        
        
        response_data = {'team_id': new_team_id, 'team_name': team_name, 'region': region}
        return format_response(response_data, 'team', 201)
    
    return jsonify(result), status_code # Return error response

# --- R: Read All Teams (GET) ---
@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Handles reading all teams."""
    query = "SELECT team_id, team_name, region FROM Teams"
    
    data, status_code = execute_query(query, fetch=True)
    
    if status_code != 200:
        return jsonify(data), status_code
        
    return format_response(data, 'teams', 200)

# --- R: Read Single Team (GET) ---
@app.route('/api/teams/<int:team_id>', methods=['GET'])
def get_team(team_id):
    """Handles reading a single team by ID."""
    query = "SELECT team_id, team_name, region FROM Teams WHERE team_id = %s"
    params = (team_id,)
    
    data, status_code = execute_query(query, params=params, fetch=True)
    
    if status_code != 200:
        return jsonify(data), status_code
    
    
    if not data:
        return make_response(jsonify({'error': f'Team with ID {team_id} not found.'}), 404)
        
    return format_response(data[0], 'team', 200)

# --- U: Update Team (PUT) ---
@app.route('/api/teams/<int:team_id>', methods=['PUT'])
def update_team(team_id):
    """Handles updating an existing team with input validation."""
    data = request.get_json()
    
    
    if not data or not any(key in data for key in ['team_name', 'region']):
        return make_response(jsonify({'error': 'No fields provided for update. Must include team_name or region.'}), 400)
    
    # Build the dynamic UPDATE query
    updates = []
    params = []
    
    if 'team_name' in data:
        updates.append("team_name = %s")
        params.append(data['team_name'])
        
    if 'region' in data:
        updates.append("region = %s")
        params.append(data['region'])
        
    query = f"UPDATE Teams SET {', '.join(updates)} WHERE team_id = %s"
    params.append(team_id)
    
    result, status_code = execute_query(query, params=tuple(params), fetch=False)
    
    if status_code != 201:
        return jsonify(result), status_code
    
    
    if result.get('rows_affected') == 0:
        # Check if the team exists before returning 404 
        team_data, _ = execute_query("SELECT team_id FROM Teams WHERE team_id = %s", (team_id,), fetch=True)
        if not team_data:
            return make_response(jsonify({'error': f'Team with ID {team_id} not found.'}), 404)
        
        return make_response(jsonify({'message': f'Team {team_id} updated, or data was identical.'}), 200)

    # Return success and the updated ID
    return make_response(jsonify({'message': f'Team {team_id} updated successfully.'}), 200)

# --- D: Delete Team (DELETE) ---
@app.route('/api/teams/<int:team_id>', methods=['DELETE'])
def delete_team(team_id):
    """Handles deleting a team by ID."""
    query = "DELETE FROM Teams WHERE team_id = %s"
    params = (team_id,)
    
    result, status_code = execute_query(query, params=params, fetch=False)
    
    if status_code != 201:
        # Check for Foreign Key constraint violation (e.g., if players are still linked)
        if 'Foreign Key' in result.get('error', ''):
             return make_response(jsonify({'error': f"Cannot delete Team {team_id}. It is still referenced by Players or Matches."}), 409) # Conflict
        return jsonify(result), status_code
    
    if result.get('rows_affected') == 0:
        return make_response(jsonify({'error': f'Team with ID {team_id} not found.'}), 404)
    
    return make_response('', 204) 


# --- 4. APPLICATION RUNNER ---

if __name__ == '__main__':
    # You may want to disable debug=True for production
    app.run(debug=True)