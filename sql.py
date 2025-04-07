import re
import ast
import pandas as pd
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from datetime import datetime

DATABASE_URL = "postgresql://technographics_dataset_user:6ygabdgGyylCn0v8WNXn42kBQLQptFHm@dpg-cvnmb0je5dus738lc100-a.oregon-postgres.render.com/technographics_dataset"
engine = create_engine(DATABASE_URL)
db = SQLDatabase.from_uri(DATABASE_URL)

tables_columns = {
    "companies": ["company_id", "name", "description", "company_size", "state", "country", "city", "zip_code", "address", "url"],
    "tools": ["tool_id", "name", "type", "created_at"],
    "company_tools": ["company_id", "tool_id", "source", "last_updated"],
}

def extract_columns(query: str) -> list[str]:
    """
    Extracts the column names from a SQL SELECT query.

    Args:
        query (str): The SQL SELECT query.

    Returns:
        list[str]: A list of column names extracted from the query.
    """
    print(f"Extracting columns from query: {query}")  # Add this line
    pattern = re.compile(r"SELECT\s+(?:DISTINCT\s+)?(.*?)\s+FROM", re.IGNORECASE | re.DOTALL)
    match = pattern.search(query)
    if not match:
        return []
    columns_string = match.group(1)
    columns = [col.strip() for col in columns_string.split(",") if col.strip()]
    print(f"Extracted columns: {columns}")  # Add this line
    return columns

def replace_null_values(columns: list, result: list) -> str:
    """
    Replaces null values in the result with default values based on column names.

    Args:
        columns (list): A list of column names.
        result (list): A list containing the query result.

    Returns:
        str: A string representation of the updated result list with null values replaced.
    """
    default_values = {
        "name": "Unknown Name",
        "type": "Other Software",  # Updated default to reflect new fallback category
        "company_name": "Unknown Company",
        "tool_name": "Unknown Tool",
        "source": "Unknown Source",
        "description": "No description available",
        "company_size": "Unknown Size",
        "state": "Unknown State",
        "country": "Unknown Country",
        "city": "Unknown City",
        "zip_code": "Unknown Zip",
        "address": "Unknown Address",
        "url": "Unknown URL",
        "last_updated": "1970-01-01 00:00:00",
    }
    df = pd.DataFrame(result, columns=columns)
    for column, default_value in default_values.items():
        if column in df.columns:
            df[column] = df[column].fillna(default_value)
    # Convert datetime objects to strings
    for col in df.columns:
        if df[col].dtype == 'object' and any(isinstance(x, datetime) for x in df[col].dropna()):
            df[col] = df[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, datetime) else x)
    return str(df.values.tolist())

def replace_wildcard(query: str) -> str:
    """
    Replaces the wildcard (*) in the SQL query with the appropriate column names.

    Args:
        query (str): The SQL query to be modified.

    Returns:
        str: The modified SQL query with the wildcard replaced.
    """
    query_upper = query.upper()
    for table, columns in tables_columns.items():
        if f"FROM {table.upper()}" in query_upper:
            if "SELECT *" in query_upper:
                column_list = ", ".join([f"{table}.{col}" for col in columns])
                # Replace SELECT * with specific columns, preserving original case in the query
                query = re.sub(
                    r"SELECT\s*\*\s*FROM",
                    f"SELECT {column_list} FROM",
                    query,
                    flags=re.IGNORECASE
                )
                print(f"Replaced wildcard with: {column_list}")  # Debug print
                break
    return query

def sql_tool(query: str):
    """
    Executes an SQL query against a PostgreSQL database and returns the results.

    Args:
        query (str): The SQL query to execute.

    Returns:
        str: A string representation of the query results, with null values replaced,
             or an error message if the query fails or returns no results.
    """
    query = replace_wildcard(query)
    result = db.run(query)
    print(f"Raw SQL Result: {result}")  # Add this line


    if not result:
        return "No results found in the database. Please try another query."

    ordered_columns = extract_columns(query)
    
    # Handle the result from db.run
    try:
        result_list = ast.literal_eval(result)
    except (ValueError, SyntaxError):
        # Fallback: assume result is already a list or handle raw string
        return f"Error parsing database result: {result}. Please refine the query."

    if not isinstance(result_list, list) or not result_list:
        return "No valid results returned from the database."

    result_str = replace_null_values(ordered_columns, result_list)
    return result_str