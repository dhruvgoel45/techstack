"""
Module Overview
---------------
This module provides a function to generate a prompt template listing available tools and their descriptions.
It informs the agent about the tools it can use to query a PostgreSQL database of companies and their tools, including usage rules.

Structure
---------
- Imports: Necessary libraries and modules.
- Function: A function to generate and return a tools prompt template.
- Example Usage: An example of how to use the function to retrieve the prompt template.

Example usage:
    from src.prompts.tools_prompt import get_tools_prompt
    from src.tools.sql import sql_tool  # Example tool import
    tools = [sql_tool]  # Assuming 'tools' is a list of tool objects

    prompt_template = get_tools_prompt(tools)

Note:
    The `get_tools_prompt` function should be called with a list of tool objects to retrieve the tools prompt template for use in the application.
"""

from langchain_core.tools import render_text_description

__all__ = ["get_tools_prompt"]


def get_tools_prompt(tools):
    names = [tool.name for tool in tools]
    names = ", ".join(names)
    descriptions = render_text_description(tools)
    return """
    As an agent you have access to the following tools:
    
    Names: {names}
    Documentation: {descriptions}
    
    Below is a detailed description of each tool and rules for using them.Rules for Using Tools:
    - Use the 'sql_tool' to execute SELECT queries against the database.
    - Pass the tool a single, syntactically correct SQL query string as input.
    - The tool returns a string with query results or an empty string if no results are found—handle this in your response.
    - Follow the schema and rules outlined in the SQL tool rules prompt when constructing queries.
    - Do not use tools for anything other than their intended purpose (e.g., no DML operations).
    
    """.format(
        names=names, descriptions=descriptions
    )
