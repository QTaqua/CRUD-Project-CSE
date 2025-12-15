from flask import Flask, jsonify, request, make_response
import mysql.connector
from flask_cors import CORS
from datetime import date, datetime, timedelta, timezone
import jwt
from functools import wraps


# --- 1. CONFIGURATION ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# JWT Configuration (Choose a strong, random key)
app.config['SECRET_KEY'] = 'YOUR_VERY_STRONG_SECRET_KEY_HERE' 
'''if want to generate a random key you can use:
import os'''

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


def get_next_id(table_name, id_column):
    """Fetches the maximum existing ID and returns the next one (max + 1)."""
    # Use a direct, simple connection just for this query to minimize overhead
    conn = get_db_connection()
    if conn is None:
        return None 
    
    cursor = conn.cursor()
    
    try:
        # Use MAX() to find the largest existing ID
        query = f"SELECT MAX({id_column}) FROM {table_name}"
        cursor.execute(query)
        
        # fetchone() returns a tuple, e.g., (105,)
        max_id = cursor.fetchone()[0] 
        
        # If max_id is None (table is empty), start at 1. Otherwise, return max + 1.
        next_id = (max_id or 0) + 1
        return next_id

    except mysql.connector.Error as err:
        print(f"Error calculating next ID: {err}")
        return None
        
    finally:
        cursor.close()
        conn.close()



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

def token_required(f):
    """
    Decorator function to secure API routes.
    It checks for a valid JWT in the Authorization header.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # JWTs are typically sent as: Authorization: Bearer <token>
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Attempt to extract the token part
                token = auth_header.split(' ')[1]
            except IndexError:
                # Header present but not in 'Bearer <token>' format
                return make_response(jsonify({'error': 'Token format is invalid. Use "Bearer <token>"'}), 401)
        
        if not token:
            return make_response(jsonify({'error': 'Token is missing'}), 401) # 401 Unauthorized

        try:
            # Decode the token using the secret key
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            # You can attach the user ID or other data to the request context here if needed
            # current_user_id = data.get('user_id') 
            pass # Token is valid
            
        except jwt.ExpiredSignatureError:
            return make_response(jsonify({'error': 'Token has expired'}), 401)

        except jwt.InvalidTokenError:
            return make_response(jsonify({'error': 'Token is invalid'}), 401)

        # Pass the execution to the original function (e.g., create_team)
        return f(*args, **kwargs)

    return decorated

# --- Token Generation/Login (POST) ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Generates a JWT upon successful authentication."""
    auth = request.get_json()
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return make_response(
            jsonify({'error': 'Missing username or password'}), 400
        )
        
    # --- Hardcoded Check ---
    if auth.get('username') == 'admin' and auth.get('password') == '12345':
        # 1. Define the payload
        payload = {
            'user_id': 1, # Example user ID
            'username': 'admin',
            'exp': datetime.now(timezone.utc) + timedelta(minutes=60), # Token expires in 60 minutes
            'iat': datetime.now(timezone.utc) # Issued at time
        }
        
        # 2. Encode the token
        token = jwt.encode(
            payload,
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        # 3. Return the token to the client
        return jsonify({'token': token})
        
    # Failed authentication
    return make_response(
        jsonify({'error': 'Could not verify'}), 401,
        {'WWW-Authenticate': 'Basic realm="Login required"'}
    )

# --- C: Create New Team (POST) ---
@app.route('/api/teams', methods=['POST'])
@token_required
def create_team():
    """Handles creating a new team with input validation and manual ID generation."""
    data = request.get_json()
    
    # Graded Requirement: Input Validation
    if not data or 'team_name' not in data or 'region' not in data:
        return make_response(jsonify({'error': 'Missing required fields: team_name and region are required.'}), 400)

    team_name = data['team_name']
    region = data['region']

    # --- MANUAL ID GENERATION START ---
    new_team_id = get_next_id("Teams", "team_id")
    
    if new_team_id is None:
        return make_response(jsonify({'error': 'Failed to calculate new team ID.'}), 500)
    # --- MANUAL ID GENERATION END ---
    
    # 🚨 CRITICAL CHANGE: Query now includes 'team_id'
    query = "INSERT INTO Teams (team_id, team_name, region) VALUES (%s, %s, %s)"
    params = (new_team_id, team_name, region) # Pass the generated ID
    
    # Note: We must change fetch=False from 201 to 200 for CUD operation messages
    result, status_code = execute_query(query, params=params, fetch=False)
    
    if status_code != 201:
        # If the query fails, return the error message
        return jsonify(result), status_code
    
    # Return 201 Created response
    response_data = {'team_id': new_team_id, 'team_name': team_name, 'region': region}
    return format_response(response_data, 'team', 201)

# --- R: Read All Teams (GET) ---
@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Handles reading all teams."""
    query = "SELECT team_id, team_name, region FROM Teams"
    
    data, status_code = execute_query(query, fetch=True)
    
    if status_code != 200:
        return jsonify(data), status_code
        
    return format_response(data, 'teams', 200)


# --- U: Update Team (PUT) ---
@app.route('/api/teams/<int:team_id>', methods=['PUT'])
@token_required
def update_team(team_id):
    """
    Handles updating an existing team (team_name or region) by ID.
    """
    data = request.get_json()
    
    # Graded Requirement: Input Validation (Check if payload exists and has fields)
    if not data or not any(key in data for key in ['team_name', 'region']):
        return make_response(jsonify({'error': 'No valid fields provided for update. Must include team_name or region.'}), 400)
    
    # 1. Build the dynamic UPDATE query based on provided fields
    updates = []
    params = []
    
    if 'team_name' in data:
        updates.append("team_name = %s")
        params.append(data['team_name'])
        
    if 'region' in data:
        updates.append("region = %s")
        params.append(data['region'])
        
    if not updates:
        return make_response(jsonify({'error': 'No updatable fields found in request body.'}), 400)

    # 2. Finalize query and parameters
    query = f"UPDATE Teams SET {', '.join(updates)} WHERE team_id = %s"
    params.append(team_id)
    
    # 3. Execute the query
    result, status_code = execute_query(query, params=tuple(params), fetch=False)
    
    if status_code != 201:
        return jsonify(result), status_code
    
    # 4. Check for 404 Not Found condition
    if result.get('rows_affected') == 0:
       
        check_query = "SELECT team_id FROM Teams WHERE team_id = %s"
        team_check, check_status = execute_query(check_query, (team_id,), fetch=True)
        
        if check_status == 200 and not team_check:
            # Team ID not existing -> 404
            return make_response(jsonify({'error': f'Team with ID {team_id} not found.'}), 404)
        
        # Team ID exists, but no change was made -> 200 OK
        return make_response(jsonify({'message': f'Team {team_id} found, but no changes were applied (data was identical).'}), 200)

    # 5. Success
    return make_response(jsonify({'message': f'Team {team_id} updated successfully.'}), 200)

# --- D: Delete Team (DELETE) ---
@app.route('/api/teams/<int:team_id>', methods=['DELETE'])
@token_required
def delete_team(team_id):
    """
    Handles deleting a team by ID.

    Returns:
    - 204 No Content on successful deletion.
    - 404 Not Found if team does not exist.
    - 409 Conflict if Foreign Key constraints prevent deletion.
    """
    query = "DELETE FROM Teams WHERE team_id = %s"
    params = (team_id,)
    
    # Execute the query. We use fetch=False as it's a CUD operation.
    result, status_code = execute_query(query, params=params, fetch=False)
    
    # The execute_query function handles general database errors (500)
    if status_code != 201:
        error_message = result.get('error', '')
        
        # Check for Foreign Key constraint violation (MySQL Error 1451 or 1452)
      
        if 'Foreign Key' in error_message or status_code == 409:
             return make_response(jsonify({
                 'error': f"Cannot delete Team {team_id}. It is still referenced by Players or Matches.",
                 'code': 'FK_VIOLATION'
             }), 409) # 409 Conflict
             
        # Return any other execution error
        return jsonify(result), status_code
    
    # If successful (status_code == 201 from execute_query), check rows_affected.
    
    # Graded Requirement: 404 Not Found for delete
    if result.get('rows_affected') == 0:
        # Check if the team existed before deletion
        check_query = "SELECT team_id FROM Teams WHERE team_id = %s"
        team_check, _ = execute_query(check_query, (team_id,), fetch=True)
        
        # If the check returns no data, the resource was not found
        if not team_check:
            return make_response(jsonify({'error': f'Team with ID {team_id} not found.'}), 404)
        
        # If rows_affected is 0 but the team was found, it means no actual change occurred (shouldn't happen with DELETE)
        # But we default to 404 if 0 rows were affected and the resource check fails.
        return make_response(jsonify({'error': f'Team with ID {team_id} not found.'}), 404)
    
    # Graded Requirement: 204 No Content
    # This indicates successful deletion with no body to return.
    return make_response('', 204)

# --- 4. APPLICATION RUNNER ---

if __name__ == '__main__':
    # You may want to disable debug=True for production
    app.run(debug=True)