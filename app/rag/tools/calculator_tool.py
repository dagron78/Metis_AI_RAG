"""
CalculatorTool - Tool for performing mathematical calculations
"""
import logging
import time
import math
import re
from typing import Any, Dict, List, Optional
import ast
import operator

from app.rag.tools.base import Tool

# Define safe operations for the calculator
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,  # Unary negation
}

# Define safe math functions
SAFE_FUNCTIONS = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'pow': pow,
    # Math module functions
    'sqrt': math.sqrt,
    'exp': math.exp,
    'log': math.log,
    'log10': math.log10,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'degrees': math.degrees,
    'radians': math.radians,
    'ceil': math.ceil,
    'floor': math.floor,
}

# Define common unit conversion factors
UNIT_CONVERSIONS = {
    # Length
    "m_to_km": 0.001,
    "km_to_m": 1000,
    "m_to_cm": 100,
    "cm_to_m": 0.01,
    "m_to_mm": 1000,
    "mm_to_m": 0.001,
    "km_to_miles": 0.621371,
    "miles_to_km": 1.60934,
    "feet_to_meters": 0.3048,
    "meters_to_feet": 3.28084,
    "inches_to_cm": 2.54,
    "cm_to_inches": 0.393701,
    
    # Weight/Mass
    "kg_to_g": 1000,
    "g_to_kg": 0.001,
    "kg_to_lb": 2.20462,
    "lb_to_kg": 0.453592,
    "oz_to_g": 28.3495,
    "g_to_oz": 0.035274,
    
    # Volume
    "l_to_ml": 1000,
    "ml_to_l": 0.001,
    "l_to_gallons": 0.264172,
    "gallons_to_l": 3.78541,
    "cubic_m_to_l": 1000,
    "l_to_cubic_m": 0.001,
    
    # Temperature
    "c_to_f": lambda c: (c * 9/5) + 32,
    "f_to_c": lambda f: (f - 32) * 5/9,
    "c_to_k": lambda c: c + 273.15,
    "k_to_c": lambda k: k - 273.15,
    
    # Time
    "hours_to_minutes": 60,
    "minutes_to_hours": 1/60,
    "days_to_hours": 24,
    "hours_to_days": 1/24,
    "minutes_to_seconds": 60,
    "seconds_to_minutes": 1/60,
    
    # Speed
    "kmh_to_ms": 0.277778,
    "ms_to_kmh": 3.6,
    "mph_to_kmh": 1.60934,
    "kmh_to_mph": 0.621371,
    
    # Area
    "sqm_to_sqkm": 0.000001,
    "sqkm_to_sqm": 1000000,
    "sqm_to_hectares": 0.0001,
    "hectares_to_sqm": 10000,
    "sqm_to_sqft": 10.7639,
    "sqft_to_sqm": 0.092903,
    "acres_to_sqm": 4046.86,
    "sqm_to_acres": 0.000247105,
}


class SafeEvaluator(ast.NodeVisitor):
    """
    Safe evaluator for mathematical expressions
    
    This class evaluates mathematical expressions in a safe way, preventing
    code execution and only allowing approved operations.
    """
    
    def __init__(self, variables=None):
        """
        Initialize the safe evaluator
        
        Args:
            variables: Dictionary of variable values
        """
        self.variables = variables or {}
    
    def visit_BinOp(self, node):
        """Visit binary operation nodes"""
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        if type(node.op) not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
        
        return SAFE_OPERATORS[type(node.op)](left, right)
    
    def visit_UnaryOp(self, node):
        """Visit unary operation nodes"""
        operand = self.visit(node.operand)
        
        if type(node.op) not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
        
        return SAFE_OPERATORS[type(node.op)](operand)
    
    def visit_Name(self, node):
        """Visit variable name nodes"""
        if node.id in self.variables:
            return self.variables[node.id]
        elif node.id in {'pi', 'e'}:
            return getattr(math, node.id)
        else:
            raise ValueError(f"Unknown variable: {node.id}")
    
    def visit_Num(self, node):
        """Visit number nodes"""
        return node.n
    
    def visit_Constant(self, node):
        """Visit constant nodes (Python 3.8+)"""
        return node.value
    
    def visit_Call(self, node):
        """Visit function call nodes"""
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are supported")
        
        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Unsupported function: {func_name}")
        
        args = [self.visit(arg) for arg in node.args]
        return SAFE_FUNCTIONS[func_name](*args)
    
    def generic_visit(self, node):
        """Reject any nodes not explicitly handled"""
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


class CalculatorTool(Tool):
    """
    Tool for performing mathematical calculations
    
    This tool supports:
    - Basic arithmetic operations (+, -, *, /, //, %, **)
    - Mathematical functions (sqrt, sin, cos, etc.)
    - Variable substitution
    - Unit conversions
    """
    
    def __init__(self):
        """
        Initialize the calculator tool
        """
        super().__init__(
            name="calculator",
            description="Performs mathematical calculations and unit conversions"
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the calculator tool
        
        Args:
            input_data: Dictionary containing:
                - expression: Mathematical expression to evaluate
                - variables: Dictionary of variable values (optional)
                - precision: Number of decimal places for the result (optional)
                - unit_conversion: Unit conversion specification (optional)
                
        Returns:
            Dictionary containing:
                - result: Calculated result
                - steps: Calculation steps (if available)
                - error: Error message (if calculation failed)
        """
        start_time = time.time()
        self.logger.info(f"Executing calculation: {input_data.get('expression')}")
        
        # Extract parameters
        expression = input_data.get("expression")
        variables = input_data.get("variables", {})
        precision = input_data.get("precision")
        unit_conversion = input_data.get("unit_conversion")
        
        # Validate input
        if not expression:
            error_msg = "Expression is required"
            self.logger.error(error_msg)
            return {"error": error_msg}
        
        try:
            # Perform the calculation
            result = self._evaluate_expression(expression, variables)
            steps = []
            
            # Apply unit conversion if specified
            if unit_conversion:
                steps.append(f"Initial result: {result}")
                result, conversion_step = self._convert_units(result, unit_conversion)
                steps.append(conversion_step)
            
            # Apply precision if specified
            if precision is not None:
                if not isinstance(precision, int) or precision < 0:
                    raise ValueError("Precision must be a non-negative integer")
                
                original_result = result
                result = round(result, precision)
                steps.append(f"Rounded to {precision} decimal places: {original_result} → {result}")
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Calculation completed in {elapsed_time:.2f}s. Result: {result}")
            
            return {
                "result": result,
                "steps": steps if steps else None,
                "execution_time": elapsed_time
            }
        except Exception as e:
            error_msg = f"Error performing calculation: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _evaluate_expression(self, expression: str, variables: Dict[str, Any]) -> float:
        """
        Safely evaluate a mathematical expression
        
        Args:
            expression: Mathematical expression
            variables: Dictionary of variable values
            
        Returns:
            Calculated result
        """
        # Clean the expression
        expression = expression.strip()
        
        # Parse the expression into an AST
        try:
            tree = ast.parse(expression, mode='eval')
            result = SafeEvaluator(variables).visit(tree.body)
            return result
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")
    
    def _convert_units(self, value: float, conversion: str) -> tuple:
        """
        Convert a value between units
        
        Args:
            value: Value to convert
            conversion: Conversion specification (e.g., "m_to_km")
            
        Returns:
            Tuple of (converted value, conversion step description)
        """
        if conversion not in UNIT_CONVERSIONS:
            raise ValueError(f"Unsupported unit conversion: {conversion}")
        
        conversion_factor = UNIT_CONVERSIONS[conversion]
        
        if callable(conversion_factor):
            # Handle special conversions like temperature
            result = conversion_factor(value)
            step = f"Converted using {conversion}: {value} → {result}"
        else:
            # Handle standard conversions
            result = value * conversion_factor
            step = f"Converted using {conversion} (factor: {conversion_factor}): {value} → {result}"
        
        return result, step
    
    def get_input_schema(self) -> Dict[str, Any]:
        """
        Get the input schema for the calculator tool
        
        Returns:
            JSON Schema for tool input
        """
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                },
                "variables": {
                    "type": "object",
                    "description": "Dictionary of variable values",
                    "additionalProperties": {
                        "type": "number"
                    }
                },
                "precision": {
                    "type": "integer",
                    "description": "Number of decimal places for the result",
                    "minimum": 0
                },
                "unit_conversion": {
                    "type": "string",
                    "description": "Unit conversion specification (e.g., 'm_to_km')",
                    "enum": list(UNIT_CONVERSIONS.keys())
                }
            },
            "required": ["expression"]
        }
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the output schema for the calculator tool
        
        Returns:
            JSON Schema for tool output
        """
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "number",
                    "description": "Calculated result"
                },
                "steps": {
                    "type": "array",
                    "description": "Calculation steps",
                    "items": {
                        "type": "string"
                    }
                },
                "execution_time": {
                    "type": "number",
                    "description": "Time taken to execute the calculation in seconds"
                },
                "error": {
                    "type": "string",
                    "description": "Error message if the calculation failed"
                }
            }
        }
    
    def get_examples(self) -> List[Dict[str, Any]]:
        """
        Get examples of calculator tool usage
        
        Returns:
            List of example input/output pairs
        """
        return [
            {
                "input": {
                    "expression": "2 + 2 * 3"
                },
                "output": {
                    "result": 8,
                    "execution_time": 0.001
                }
            },
            {
                "input": {
                    "expression": "sqrt(16) + pow(2, 3)"
                },
                "output": {
                    "result": 12.0,
                    "execution_time": 0.001
                }
            },
            {
                "input": {
                    "expression": "sin(radians(30))",
                    "precision": 2
                },
                "output": {
                    "result": 0.5,
                    "steps": ["Rounded to 2 decimal places: 0.49999999999999994 → 0.5"],
                    "execution_time": 0.001
                }
            },
            {
                "input": {
                    "expression": "x * y + z",
                    "variables": {"x": 2, "y": 3, "z": 5}
                },
                "output": {
                    "result": 11,
                    "execution_time": 0.001
                }
            },
            {
                "input": {
                    "expression": "100",
                    "unit_conversion": "km_to_miles"
                },
                "output": {
                    "result": 62.1371,
                    "steps": [
                        "Initial result: 100",
                        "Converted using km_to_miles (factor: 0.621371): 100 → 62.1371"
                    ],
                    "execution_time": 0.001
                }
            },
            {
                "input": {
                    "expression": "25",
                    "unit_conversion": "c_to_f"
                },
                "output": {
                    "result": 77.0,
                    "steps": [
                        "Initial result: 25",
                        "Converted using c_to_f: 25 → 77.0"
                    ],
                    "execution_time": 0.001
                }
            }
        ]