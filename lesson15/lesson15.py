import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
from neo4j import GraphDatabase

load_dotenv()
KLUCZ = os.getenv("KLUCZ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REPORT_URL = os.getenv("REPORT_URL")
SQL_API_URL = os.getenv("SQL_API_URL")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


client = OpenAI(api_key=os.getenv(f"{OPENAI_API_KEY}"))
neo4j_driver = GraphDatabase.driver(
    f"{NEO4J_URI}", 
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD), 
    encrypted=False
    )


#Polecenia SQL:
#show tables = zwraca listę tabel
#show create table NAZWA_TABELI = pokazuje, jak zbudowana jest konkretna tabela
#select * from users limit 1

def sql_query(query):
    response = requests.post(
        f"{SQL_API_URL}",
        json={
            "task": "database",
            "apikey": KLUCZ,
            "query": query
        }
    )
    return response.json()

def neo4j_query(query, params):
    with neo4j_driver.session() as session:
        # Execute the query and collect results immediately
        result = session.run(query, params)
        try:
            # Collect all records into a list before the session closes
            return list(result)
        except Exception as e:
            print(f"Error executing query: {e}")
            return []

def create_graph():
    # Clear existing data
    neo4j_query("MATCH (n) DETACH DELETE n", {})
    
    # Create user nodes
    for user in users['reply']:
        query = """
        CREATE (u:User {id: $id, name: $name})
        """
        params = {"id": user['id'], "name": user['username']}
        neo4j_query(query, params)
    
    # Create relationships
    for conn in connections['reply']:
        query = """
        MATCH (u1:User {id: $user1_id})
        MATCH (u2:User {id: $user2_id})
        CREATE (u1)-[:KNOWS]->(u2)
        """
        params = {
            "user1_id": conn['user1_id'],
            "user2_id": conn['user2_id']
        }
        neo4j_query(query, params)

def find_shortest_path(from_id, to_id):
    query = """
    MATCH path = shortestPath(
        (start:User {id: $from_id})-[:KNOWS*]-(end:User {id: $to_id})
    )
    RETURN [node in nodes(path) | node.name] as names,
           length(path) as path_length
    """
    
    # Execute query and get results
    results = neo4j_query(query, {"from_id": from_id, "to_id": to_id})
    
    if results:
        path_data = results[0]  # Get first record
        return {
            "names": path_data["names"],
            "length": path_data["path_length"]
        }
    return None

def find_user_by_name(name):
    for user in users['reply']:
        if user['username'] == name:
            return user['id']
    return None

connections = sql_query("select * from connections")
users = sql_query("select * from users")

#print("Users data:", users)
#print("Connections data:", connections)

create_graph()
rafal_id = find_user_by_name('Rafał')
barbara_id = find_user_by_name('Barbara')
print(f"Rafał's ID: {rafal_id}")
print(f"Barbara's ID: {barbara_id}")

path = find_shortest_path(rafal_id, barbara_id)
if path:
    answer = ', '.join(path['names'])
    print(f"Shortest path: {' -> '.join(path['names'])} (length: {path['length']})")
else:
    answer = "No path found"
    print("No path found")
    
print(answer)

neo4j_driver.close()

json = {
    "task": "connections",
    "apikey": KLUCZ,
    "answer": answer
}

finnish = requests.post(f"{REPORT_URL}", json=json)
print(finnish.json())
