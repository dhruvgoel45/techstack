
"""
Module Overview
---------------
This module provides a function to generate a few-shot prompt template for creating SQL queries based on user inputs.
It uses LangChain's FewShotPromptTemplate and SemanticSimilarityExampleSelector to construct the prompt, tailored to a PostgreSQL database of companies and their tools.

Structure
---------
- Imports: Necessary libraries and modules.
- Function: A function to provide example input-query pairs based on the updated database schema.
- Prompt: A function to generate and return a few-shot prompt template for SQL queries.

Example usage:
    from prompts.few_shot_queries_prompt import get_few_shot_queries_prompt

    prompt_template = get_few_shot_queries_prompt()

Note:
    The get_few_shot_queries_prompt function should be called to retrieve the prompt template for use in the application.
"""

from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_openai import OpenAIEmbeddings

__all__ = ["get_few_shot_queries_prompt"]


def get_examples():
    return [
        {
            "input": "List all companies using TCP/IP.",
            "query": """SELECT DISTINCT c.name 
                        FROM company c 
                        JOIN company_tools ct ON c.company_id = ct.company_id 
                        JOIN tools t ON ct.tool_id = t.tool_id 
                        WHERE t.name = 'TCP/IP';"""
        },
        {
            "input": "Which companies use software tools?",
            "query": """SELECT DISTINCT c.name 
                        FROM company c 
                        JOIN company_tools ct ON c.company_id = ct.company_id 
                        JOIN tools t ON ct.tool_id = t.tool_id 
                        WHERE t.type = 'Software';"""
        },
        {
            "input": "What technologies does 'AAA-The Auto Club Group' use?",
            "query": """SELECT DISTINCT t.name 
                        FROM tools t 
                        JOIN company_tools ct ON t.tool_id = ct.tool_id 
                        JOIN company c ON ct.company_id = c.company_id 
                        WHERE c.name = 'AAA-The Auto Club Group';"""
        },
        {
            "input": "Find all tools used by companies sourced from LinkedIn scraped data.",
            "query": """SELECT DISTINCT t.name 
                        FROM tools t 
                        JOIN company_tools ct ON t.tool_id = ct.tool_id 
                        WHERE ct.source = 'linkedin scraped data';"""
        },
        {
            "input": "List companies that use software tools created after April 1, 2025.",
            "query": """SELECT DISTINCT c.name 
                        FROM company c 
                        JOIN company_tools ct ON c.company_id = ct.company_id 
                        JOIN tools t ON ct.tool_id = t.tool_id 
                        WHERE t.type = 'Software' 
                        AND t.created_at > '2025-04-01';"""
        },
        {
            "input": "Which companies are based in the United States?",
             "query": """SELECT DISTINCT c.name 
                FROM companies c 
                WHERE c.country = 'US';
                """
        },
       {
            "input": "give me company details about AbbVie",
            "query": """SELECT c.company_id, c.name, c.description, c.company_size, c.state, c.country, c.city, c.zip_code, c.address, c.url
                        FROM companies  C
                        WHERE c.name ILIKE 'AbbVie';"""
        },
        {
            "input": "give me details of the company accelant",
            "query": """ELECT c.company_id, c.name, c.description, c.company_size, c.state, c.country, c.city, c.zip_code, c.address, c.url
                        FROM companies  C
                        WHERE c.name ILIKE 'accelant';"""
        },
        {
            "input": "give me company size of the name",
            "query": """SELECT name, company_size 
FROM companies 
WHERE name = 'name'"""
        },

        {
            "input": "Show all tools used by companies created before April 2, 2025.",
            "query": """SELECT DISTINCT t.name 
                        FROM tools t 
                        JOIN company_tools ct ON t.tool_id = ct.tool_id 
                        JOIN company c ON ct.company_id = c.company_id 
                        WHERE c.created_at < '2025-04-02';"""
        }
    ]


def get_few_shot_queries_prompt():
    system_few_shot_prefix = """
    Given an input question, create a syntactically correct SQL query to run against a PostgreSQL database containing 'company', 'tools', and 'company_tools' tables. Use the provided SQL tool to fetch data and return accurate answers based on the query results. Unless the user specifies a number of examples, limit your query to at most {top_k} results, ordering by a relevant column if applicable. Only select the relevant columns needed to answer the question—do not query all columns unnecessarily.

    You have access to the following tables:
    - 'companies': company_id (UUID), name (STRING),  description (STRING), company_size (STRING), state (STRING), country (STRING), city (STRING), zip_code (STRING), address (STRING), url (STRING)
    - 'tools': tool_id (UUID), name (STRING), type (STRING), created_at (TIMESTAMP)
    - 'company_tools': company_id (UUID), tool_id (UUID), source (STRING), last_updated (TIMESTAMP)

    there are no tool and company names inside the company_tools table, only the company_id and tool_id are present. The company name and tool name are redundant but stored for convenience.

    Use JOINs to connect tables as needed. For case-insensitive text matching, use ILIKE with wildcards (e.g., '%Microsoft%'). Double-check your query for correctness before execution. If an error occurs, rewrite and retry. Only use SELECT statements—do not make DML statements (INSERT, UPDATE, DELETE, DROP, etc.).

    Here are some examples of user inputs and their corresponding SQL queries to guide your responses:
    """.format(
        top_k=3
    )

    example_selector = SemanticSimilarityExampleSelector.from_examples(
        get_examples(),
        OpenAIEmbeddings(model="text-embedding-ada-002"),
        FAISS,
        k=5,
        input_keys=["input"],
    )

    return FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=PromptTemplate.from_template(
            "User input: {input}\nSQL query: {query}"
        ),
        input_variables=["input"],
        prefix=system_few_shot_prefix,
        suffix="",
    )
