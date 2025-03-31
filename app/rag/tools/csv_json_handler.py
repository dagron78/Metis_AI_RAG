"""
CSV and JSON data handling utilities for the async DatabaseTool
"""
import csv
import json
import asyncio
import aiofiles
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
import logging

logger = logging.getLogger(__name__)

class AsyncCSVHandler:
    """Async-friendly CSV file handler"""
    
    @staticmethod
    async def read_csv(file_path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Read a CSV file asynchronously and return rows and column names
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Tuple of (rows as dicts, column names)
        """
        async with aiofiles.open(file_path, 'r', newline='') as f:
            content = await f.read()
        
        # Process CSV content
        reader = csv.reader(content.splitlines())
        rows = list(reader)
        
        if not rows:
            return [], []
        
        # First row contains column names
        headers = rows[0]
        
        # Convert rows to list of dictionaries
        data = []
        for row in rows[1:]:
            # Skip empty rows
            if not row:
                continue
                
            # Create a dictionary for each row
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers):
                    # Keep values as strings to match CSV format
                    row_dict[headers[i]] = value
            
            data.append(row_dict)
        
        return data, headers
    
    @staticmethod
    async def create_table_from_csv(conn, table_name: str, file_path: str) -> Tuple[List[str], int]:
        """
        Create a SQLite table from a CSV file
        
        Args:
            conn: SQLite connection
            table_name: Name of the table to create
            file_path: Path to the CSV file
            
        Returns:
            Tuple of (column names, number of rows inserted)
        """
        # Read CSV data
        data, headers = await AsyncCSVHandler.read_csv(file_path)
        
        if not data or not headers:
            return [], 0
        
        # Determine column types based on first row
        column_types = {}
        for header in headers:
            column_types[header] = "TEXT"  # Default type
            
        for row in data[:10]:  # Sample first 10 rows to determine types
            for header in headers:
                if header in row:
                    value = row[header]
                    if isinstance(value, int):
                        column_types[header] = "INTEGER"
                    elif isinstance(value, float):
                        column_types[header] = "REAL"
        
        # Create table
        columns_sql = ", ".join([f'"{h}" {column_types[h]}' for h in headers])
        create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql})'
        
        await conn.execute(create_table_sql)
        
        # Insert data in batches
        batch_size = 100
        rows_inserted = 0
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            if not batch:
                continue
                
            # Prepare placeholders for the INSERT statement
            placeholders = ", ".join(["?" for _ in headers])
            column_names = ", ".join([f'"{h}"' for h in headers])
            insert_sql = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'
            
            # Prepare values for each row
            values = []
            for row in batch:
                row_values = []
                for header in headers:
                    row_values.append(row.get(header, None))
                values.append(row_values)
            
            # Execute the INSERT statement for the batch
            await conn.executemany(insert_sql, values)
            
            rows_inserted += len(batch)
        
        await conn.commit()
        return headers, rows_inserted


class AsyncJSONHandler:
    """Async-friendly JSON file handler"""
    
    @staticmethod
    async def read_json(file_path: str) -> Any:
        """
        Read a JSON file asynchronously
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed JSON data
        """
        async with aiofiles.open(file_path, 'r') as f:
            content = await f.read()
        
        return json.loads(content)
    
    @staticmethod
    async def create_table_from_json(conn, table_name: str, file_path: str) -> Tuple[List[str], int]:
        """
        Create a SQLite table from a JSON file
        
        Args:
            conn: SQLite connection
            table_name: Name of the table to create
            file_path: Path to the JSON file
            
        Returns:
            Tuple of (column names, number of rows inserted)
        """
        # Read JSON data
        data = await AsyncJSONHandler.read_json(file_path)
        
        # Convert to list of dictionaries if it's not already
        if isinstance(data, dict):
            # Check if it's a nested structure
            if any(isinstance(v, (list, dict)) for v in data.values()):
                # For complex nested structures, we'll flatten one level
                flattened_data = []
                for key, value in data.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                item_copy = item.copy()
                                item_copy['_parent_key'] = key
                                flattened_data.append(item_copy)
                    elif isinstance(value, dict):
                        value_copy = value.copy()
                        value_copy['_key'] = key
                        flattened_data.append(value_copy)
                
                if flattened_data:
                    data = flattened_data
                else:
                    # If we couldn't flatten, just use the original dict
                    data = [data]
            else:
                # Simple key-value pairs
                data = [data]
        
        if not isinstance(data, list):
            raise ValueError("JSON data could not be converted to a list of records")
        
        if not data:
            return [], 0
        
        # Get all possible column names from all records
        all_columns = set()
        for item in data:
            if isinstance(item, dict):
                all_columns.update(item.keys())
        
        headers = list(all_columns)
        
        # Determine column types based on first few records
        column_types = {}
        for header in headers:
            column_types[header] = "TEXT"  # Default type
            
        for item in data[:10]:  # Sample first 10 items to determine types
            if not isinstance(item, dict):
                continue
                
            for header in headers:
                if header in item:
                    value = item[header]
                    if isinstance(value, int):
                        column_types[header] = "INTEGER"
                    elif isinstance(value, float):
                        column_types[header] = "REAL"
                    elif isinstance(value, bool):
                        column_types[header] = "INTEGER"  # SQLite doesn't have a boolean type
                    elif isinstance(value, (list, dict)):
                        # Store complex types as JSON strings
                        column_types[header] = "TEXT"
        
        # Create table
        columns_sql = ", ".join([f'"{h}" {column_types[h]}' for h in headers])
        create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql})'
        
        await conn.execute(create_table_sql)
        
        # Insert data in batches
        batch_size = 100
        rows_inserted = 0
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            if not batch:
                continue
                
            # Prepare placeholders for the INSERT statement
            placeholders = ", ".join(["?" for _ in headers])
            column_names = ", ".join([f'"{h}"' for h in headers])
            insert_sql = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'
            
            # Prepare values for each row
            values = []
            for item in batch:
                if not isinstance(item, dict):
                    continue
                    
                row_values = []
                for header in headers:
                    value = item.get(header, None)
                    # Convert complex types to JSON strings
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    # Convert boolean to integer
                    elif isinstance(value, bool):
                        value = 1 if value else 0
                    row_values.append(value)
                values.append(row_values)
            
            # Execute the INSERT statement for the batch
            await conn.executemany(insert_sql, values)
            
            rows_inserted += len(batch)
        
        await conn.commit()
        return headers, rows_inserted