"""
Module Overview
---------------
This module provides a function to generate a system prompt template containing rules for using the SQL tool.
The prompt guides the agent on how to interact with a PostgreSQL database containing company and tool information, ensuring proper syntax and constraints.

Structure
---------
- Imports: Necessary libraries and modules (if any).
- Function: A function to generate and return the SQL tool rules prompt template.
- Example Usage: An example of how to use the function to retrieve the prompt template.

Example usage:
    from prompts.sql_tool_rules_prompt import get_sql_tool_rules_prompt

    prompt_template = get_sql_tool_rules_prompt()

Note:
    The `get_sql_tool_rules_prompt` function should be called to retrieve the SQL tool rules prompt template for use in the application.
"""

__all__ = ["get_sql_tool_rules_prompt"]


def get_sql_tool_rules_prompt():
    return """\
    The SQL tool enables interaction with a PostgreSQL database containing information about companies and the tools they use. You can query the database schema, columns, and values. The tool will return a string containing the query results or an empty string if no results are found—act accordingly.

    Here’s an overview of the tables in the database:

    - 'companies': Stores information about companies.
      Columns:
      - company_id (string): Unique identifier for the company (UUID format).
      - name (string): Name of the company (e.g., 'Abbott', 'Abboud Trading'). (Used for identifying existing records)
      - description (string): A brief description of the company.
      - company_size (string): The size of the company (e.g., 'Small', 'Medium', 'Large').
      - state (string): The state where the company is located.
      - country (string): The country where the company operates.
      - city (string): The city where the company is headquartered.
      - zip_code (string): The postal code of the company's location.
      - address (string): The physical address of the company.
      - url (string): The official website of the company.
      - created_at (datetime): Timestamp indicating when the company record was created (e.g., '2025-04-02 03:29:12.604245'). (Remains unchanged when updating existing records)

    - 'tools': Stores information about tools used by companies.
      Columns:
      - tool_id (string): Unique identifier for the tool.
      - name (string): Name of the tool (e.g., 'Microsoft PowerPoint', 'AWS').
      - type (string): Type of the tool (e.g., 'Software').
      - created_at (datetime): Timestamp of when the tool record was created (e.g., '2025-04-02 03:29:12.090996').

    - 'company_tools': Links companies to the tools they use.
      Columns:
      - company_id (string): Foreign key referencing 'companies.company_id'.
      - tool_id (string): Foreign key referencing 'tools.tool_id'.
      - source (string): Source of the data (e.g., 'linkedin scraped data').
      - last_updated (datetime): Timestamp of the last update (e.g., '2025-04-02 03:24:20.532202').

    About the values in the database:
    - 'companies':
    - company_id: Unique UUID strings (e.g., '550e8400-e29b-41d4-a716-446655440000').
      - name: Unique company names (e.g., 'Abbott', 'Abboud Trading').
      - description: Text describing the company’s purpose or industry (e.g., 'Pharmaceutical company', 'Trading firm').
      - company_size: Categories like 'Small', 'Medium', 'Large', or specific employee counts if available (e.g., '50-200').
      - state: State or province codes/names (e.g., 'CA' for California, 'NY' for New York).
      - country: Country codes or names (e.g., 'US', 'Canada').
      - city: City names (e.g., 'San Francisco', 'Toronto').
      - zip_code: Postal codes (e.g., '94105', 'M5V 2T6').
      - address: Full street addresses (e.g., '123 Main St, San Francisco, CA 94105').
      - url: Company website URLs (e.g., 'https://abbott.com', 'http://abboudtrading.com').
      - created_at: Any valid datetime, typically recent (e.g., around April 2025 based on current data, such as '2025-04-02 03:29:12.604245').
    - 'tools':
      - name: Tool names (e.g., 'Microsoft PowerPoint', 'AWS').
      - type: Typically 'Software', but could include other types in the future.
      - created_at: Any valid datetime, typically recent.
    - 'company_tools':
      - source: Data origins like 'linkedin scraped data' or other sources.
      - last_updated: Any valid datetime, typically recent.

 When using this tool, you must:
    - Always use correct SQL syntax for PostgreSQL.
    - Use JOINs to connect 'companies', 'tools', and 'company_tools' as needed, using id columns for joins (e.g., company_id, tool_id).
    - For case-insensitive text matching, use ILIKE with wildcards (e.g., '%Microsoft%').
    - Always query only the tables and columns mentioned above—no others.
   - **CRITICAL: Never use the wildcard '*' in the generated query; always specify the exact columns needed to answer the question.**
    - Never make DML statements (INSERT, UPDATE, DELETE, DROP, etc.)—only SELECT statements are allowed.
    - Limit results to 100 rows unless the user specifies otherwise, ordering by a relevant column if applicable.
    - Double-check your query before execution; if an error occurs, rewrite and retry.
    - Correct the user’s input if it’s unclear or misaligned with the schema (e.g., if they ask for a tool not in the 'tools' table).
    - Never repeat the same query twice in a row; if the first attempt fails, try a different approach.
    - Answer only what the user asks for—do not provide extra information unless requested.
    """