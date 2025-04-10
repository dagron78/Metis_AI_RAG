"""
Unit tests for the CalculatorTool
"""
import pytest
import math
from unittest.mock import MagicMock, AsyncMock

from app.rag.tools import CalculatorTool


class TestCalculatorTool:
    """Tests for the CalculatorTool implementation"""
    
    @pytest.mark.asyncio
    async def test_basic_arithmetic(self):
        """Test basic arithmetic operations"""
        calculator = CalculatorTool()
        
        # Test addition
        result = await calculator.execute({"expression": "2 + 3"})
        assert "result" in result
        assert result["result"] == 5
        
        # Test subtraction
        result = await calculator.execute({"expression": "10 - 4"})
        assert result["result"] == 6
        
        # Test multiplication
        result = await calculator.execute({"expression": "3 * 5"})
        assert result["result"] == 15
        
        # Test division
        result = await calculator.execute({"expression": "20 / 4"})
        assert result["result"] == 5
        
        # Test order of operations
        result = await calculator.execute({"expression": "2 + 3 * 4"})
        assert result["result"] == 14
        
        # Test parentheses
        result = await calculator.execute({"expression": "(2 + 3) * 4"})
        assert result["result"] == 20
    
    @pytest.mark.asyncio
    async def test_math_functions(self):
        """Test mathematical functions"""
        calculator = CalculatorTool()
        
        # Test square root
        result = await calculator.execute({"expression": "sqrt(16)"})
        assert result["result"] == 4
        
        # Test power
        result = await calculator.execute({"expression": "pow(2, 3)"})
        assert result["result"] == 8
        
        # Test trigonometric functions
        result = await calculator.execute({"expression": "sin(radians(30))"})
        assert math.isclose(result["result"], 0.5, abs_tol=1e-10)
        
        result = await calculator.execute({"expression": "cos(radians(60))"})
        assert math.isclose(result["result"], 0.5, abs_tol=1e-10)
        
        # Test logarithmic functions
        result = await calculator.execute({"expression": "log10(100)"})
        assert result["result"] == 2
    
    @pytest.mark.asyncio
    async def test_variables(self):
        """Test variable substitution"""
        calculator = CalculatorTool()
        
        # Test simple variable
        result = await calculator.execute({
            "expression": "x + 5",
            "variables": {"x": 10}
        })
        assert result["result"] == 15
        
        # Test multiple variables
        result = await calculator.execute({
            "expression": "x * y + z",
            "variables": {"x": 2, "y": 3, "z": 4}
        })
        assert result["result"] == 10
        
        # Test variables in functions
        result = await calculator.execute({
            "expression": "sqrt(x) + pow(y, 2)",
            "variables": {"x": 16, "y": 3}
        })
        assert result["result"] == 13
    
    @pytest.mark.asyncio
    async def test_unit_conversion(self):
        """Test unit conversions"""
        calculator = CalculatorTool()
        
        # Test length conversion
        result = await calculator.execute({
            "expression": "5",
            "unit_conversion": "km_to_miles"
        })
        assert math.isclose(result["result"], 3.10686, abs_tol=1e-5)
        assert "steps" in result
        assert len(result["steps"]) == 2
        
        # Test temperature conversion
        result = await calculator.execute({
            "expression": "100",
            "unit_conversion": "c_to_f"
        })
        assert result["result"] == 212.0
        assert "steps" in result
        assert len(result["steps"]) == 2
        
        # Test weight conversion
        result = await calculator.execute({
            "expression": "10",
            "unit_conversion": "kg_to_lb"
        })
        assert math.isclose(result["result"], 22.0462, abs_tol=1e-4)
    
    @pytest.mark.asyncio
    async def test_precision(self):
        """Test result precision"""
        calculator = CalculatorTool()
        
        # Test with precision
        result = await calculator.execute({
            "expression": "1 / 3",
            "precision": 2
        })
        assert result["result"] == 0.33
        assert "steps" in result
        assert len(result["steps"]) == 1
        
        # Test with precision and unit conversion
        result = await calculator.execute({
            "expression": "10",
            "unit_conversion": "km_to_miles",
            "precision": 3
        })
        assert result["result"] == 6.214
        assert "steps" in result
        assert len(result["steps"]) == 3  # Initial result, conversion, and rounding
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling"""
        calculator = CalculatorTool()
        
        # Test division by zero
        result = await calculator.execute({"expression": "1 / 0"})
        assert "error" in result
        
        # Test invalid expression
        result = await calculator.execute({"expression": "1 + * 2"})
        assert "error" in result
        
        # Test invalid function
        result = await calculator.execute({"expression": "invalid_func(10)"})
        assert "error" in result
        
        # Test missing required parameter
        result = await calculator.execute({})
        assert "error" in result
        
        # Test invalid unit conversion
        result = await calculator.execute({
            "expression": "10",
            "unit_conversion": "invalid_conversion"
        })
        assert "error" in result
    
    def test_calculator_schemas(self):
        """Test calculator tool schemas"""
        calculator = CalculatorTool()
        
        # Check input schema
        input_schema = calculator.get_input_schema()
        assert input_schema["type"] == "object"
        assert "expression" in input_schema["properties"]
        assert "variables" in input_schema["properties"]
        assert "precision" in input_schema["properties"]
        assert "unit_conversion" in input_schema["properties"]
        assert input_schema["required"] == ["expression"]
        
        # Check output schema
        output_schema = calculator.get_output_schema()
        assert output_schema["type"] == "object"
        assert "result" in output_schema["properties"]
        assert "steps" in output_schema["properties"]
        assert "execution_time" in output_schema["properties"]
        assert "error" in output_schema["properties"]
        
        # Check examples
        examples = calculator.get_examples()
        assert len(examples) > 0
        assert "input" in examples[0]
        assert "output" in examples[0]