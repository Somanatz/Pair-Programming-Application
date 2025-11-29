"""
Pydantic Models for Request/Response Validation
================================================
Defines data schemas for API endpoints and WebSocket messages.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ==================== API MODELS ====================

class RoomCreateRequest(BaseModel):
    """Request model for creating a new room"""
    language: Optional[str] = Field(default="python", description="Programming language")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "python"
            }
        }


class RoomCreateResponse(BaseModel):
    """Response model after creating a room"""
    roomId: str = Field(..., description="Unique 8-character room ID")
    message: str = Field(default="Room created successfully")
    
    class Config:
        json_schema_extra = {
            "example": {
                "roomId": "a3b4c5d6",
                "message": "Room created successfully"
            }
        }


class AutocompleteRequest(BaseModel):
    """Request model for AI autocomplete suggestions"""
    code: str = Field(..., description="Current code content")
    cursorPosition: int = Field(..., description="Cursor position in code", ge=0)
    language: str = Field(default="python", description="Programming language")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "def hello",
                "cursorPosition": 9,
                "language": "python"
            }
        }


class AutocompleteResponse(BaseModel):
    """Response model with autocomplete suggestion"""
    suggestion: str = Field(..., description="Code suggestion")
    confidence: float = Field(default=0.8, description="Confidence score", ge=0, le=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "suggestion": "():\n    pass",
                "confidence": 0.85
            }
        }


# ==================== WEBSOCKET MODELS ====================

class WSMessage(BaseModel):
    """Base WebSocket message structure"""
    type: str = Field(..., description="Message type: init, code_update, cursor_move")
    roomId: str = Field(..., description="Room identifier")


class CodeUpdateMessage(WSMessage):
    """WebSocket message for code updates"""
    code: str = Field(..., description="Updated code content")
    cursorPosition: Optional[int] = Field(default=0, description="Cursor position")
    userId: Optional[str] = Field(default=None, description="User identifier")


class CursorMoveMessage(WSMessage):
    """WebSocket message for cursor position updates"""
    cursorPosition: int = Field(..., description="New cursor position")
    userId: Optional[str] = Field(default=None, description="User identifier")


# ==================== HELPER FUNCTIONS ====================

def get_mock_autocomplete(code: str, cursor_pos: int, language: str) -> dict:
    """
    Mock AI Autocomplete - Returns rule-based suggestions
    =====================================================
    
    This is a PROTOTYPE implementation using pattern matching.
    In production, this would integrate with:
    - OpenAI Codex API
    - GitHub Copilot
    - TabNine
    - Amazon CodeWhisperer
    
    Args:
        code: Current code content
        cursor_pos: Current cursor position
        language: Programming language
        
    Returns:
        Dictionary with suggestion and confidence score
    """
    
    # Extract text before cursor
    text_before_cursor = code[:cursor_pos] if cursor_pos <= len(code) else code
    lines = text_before_cursor.split('\n')
    current_line = lines[-1].strip() if lines else ""
    
    # ==================== PYTHON AUTOCOMPLETE SUGGESTIONS ====================
    
    if language == "python":
        suggestions = {
            # FUNCTION DEFINITIONS
            "def ": ("function_name(arg1, arg2):\n    \"\"\"\n    Function description\n    \"\"\"\n    pass", 0.92),
            "def main": ("def main():\n    \"\"\"\n    Main entry point\n    \"\"\"\n    pass\n\nif __name__ == '__main__':\n    main()", 0.95),
            "async def ": ("async_function():\n    \"\"\"\n    Async function\n    \"\"\"\n    await something()", 0.90),
            
            # CLASS DEFINITIONS
            "class ": ("ClassName:\n    \"\"\"\n    Class description\n    \"\"\"\n    def __init__(self, param):\n        self.param = param\n    \n    def method(self):\n        pass", 0.93),
            
            # LOOP CONSTRUCTS
            "for ": ("i in range(10):\n    print(i)", 0.94),
            "for i in range": ("for i in range(len(items)):\n    print(items[i])", 0.92),
            "for item in ": ("for item in items:\n    print(item)", 0.93),
            "while ": ("condition:\n    # Loop body\n    pass", 0.90),
            "while True": ("while True:\n    # Infinite loop\n    break  # Exit condition", 0.91),
            
            # CONDITIONAL STATEMENTS
            "if ": ("condition:\n    # True block\n    pass", 0.93),
            "if __name__": ("if __name__ == '__main__':\n    main()", 0.96),
            "elif ": ("condition:\n    # Elif block\n    pass", 0.91),
            "else": ("else:\n    # Else block\n    pass", 0.92),
            
            # TRY-EXCEPT BLOCKS
            "try": ("try:\n    # Try block\n    pass\nexcept Exception as e:\n    print(f'Error: {e}')", 0.94),
            "except": ("except Exception as e:\n    print(f'Error: {e}')", 0.93),
            "finally": ("finally:\n    # Cleanup code\n    pass", 0.91),
            
            # CONTEXT MANAGERS
            "with ": ("open('file.txt', 'r') as f:\n    content = f.read()", 0.92),
            "with open": ("with open('file.txt', 'r') as f:\n    content = f.read()", 0.94),
            
            # IMPORT STATEMENTS
            "import ": ("numpy as np", 0.85),
            "import numpy": ("import numpy as np", 0.95),
            "import pandas": ("import pandas as pd", 0.95),
            "import matplotlib": ("import matplotlib.pyplot as plt", 0.94),
            "from ": ("module import function", 0.86),
            "from typing": ("from typing import List, Dict, Optional", 0.93),
            
            # COMMON FUNCTIONS
            "print": ("print()", 0.96),
            "print(": ("print(f'')", 0.94),
            "return": ("return result", 0.93),
            "return None": ("return None", 0.92),
            "raise ": ("ValueError('Invalid input')", 0.91),
            "assert ": ("condition, 'Error message'", 0.90),
            
            # LIST COMPREHENSIONS
            "[": ("[x for x in items if condition]", 0.88),
            "[x for": ("[x for x in items if condition]", 0.91),
            
            # DICTIONARY OPERATIONS
            "{": ("{'key': 'value'}", 0.87),
            
            # LAMBDA FUNCTIONS
            "lambda": ("lambda x: x * 2", 0.90),
            "lambda x": ("lambda x: x * 2", 0.92),
            
            # DECORATORS
            "@": ("decorator\ndef function():\n    pass", 0.89),
            "@property": ("@property\ndef property_name(self):\n    return self._value", 0.93),
            "@staticmethod": ("@staticmethod\ndef static_method():\n    pass", 0.92),
            "@classmethod": ("@classmethod\ndef class_method(cls):\n    pass", 0.92),
            
            # STRING FORMATTING
            "f'": ("f'{variable}'", 0.93),
            "f\"": ("f\"{variable}\"", 0.93),
            
            # FILE OPERATIONS
            "open(": ("open('filename.txt', 'r') as f:\n    content = f.read()", 0.92),
            
            # DATA STRUCTURES
            "list": ("list_name = []", 0.88),
            "dict": ("dict_name = {}", 0.88),
            "set": ("set_name = set()", 0.87),
            "tuple": ("tuple_name = ()", 0.87),
            
            # COMMON PATTERNS
            "if not ": ("if not condition:\n    pass", 0.91),
            "is None": ("is None:", 0.92),
            "is not None": ("is not None:", 0.92),
            "in range": ("in range(10):", 0.93),
            
            # ASYNC/AWAIT
            "await ": ("await async_function()", 0.91),
            
            # TYPE HINTS
            "-> ": ("-> ReturnType:", 0.89),
            ": List": (": List[str]", 0.90),
            ": Dict": (": Dict[str, Any]", 0.90),
            
            # COMMON METHODS
            ".append": (".append(item)", 0.93),
            ".extend": (".extend(items)", 0.92),
            ".split": (".split(',')", 0.93),
            ".join": (".join(items)", 0.92),
            ".strip": (".strip()", 0.93),
            ".format": (".format(arg1, arg2)", 0.91),
            ".get": (".get('key', default_value)", 0.92),
            
            # OPERATORS
            "and ": ("and condition", 0.91),
            "or ": ("or condition", 0.91),
            "not ": ("not condition", 0.91),
            
            # COMMON LIBRARIES
            "pd.": ("pd.read_csv('file.csv')", 0.89),
            "np.": ("np.array([1, 2, 3])", 0.89),
            "plt.": ("plt.plot(x, y)", 0.89),
        }
    
    # ==================== JAVASCRIPT AUTOCOMPLETE (Optional) ====================
    
    elif language == "javascript" or language == "typescript":
        suggestions = {
            # FUNCTION DEFINITIONS
            "function ": ("functionName(param1, param2) {\n    // Function body\n    return result;\n}", 0.92),
            "const ": ("variableName = value;", 0.90),
            "let ": ("variableName = value;", 0.90),
            "var ": ("variableName = value;", 0.88),
            
            # ARROW FUNCTIONS
            "=> ": ("(param) => {\n    return result;\n}", 0.91),
            
            # LOOPS
            "for ": ("(let i = 0; i < array.length; i++) {\n    console.log(array[i]);\n}", 0.93),
            "for (let": ("for (let i = 0; i < array.length; i++) {\n    console.log(array[i]);\n}", 0.94),
            "forEach": ("forEach((item) => {\n    console.log(item);\n});", 0.92),
            "while ": ("(condition) {\n    // Loop body\n}", 0.90),
            
            # CONDITIONALS
            "if ": ("(condition) {\n    // True block\n}", 0.92),
            "else if": ("else if (condition) {\n    // Else if block\n}", 0.91),
            "else": ("else {\n    // Else block\n}", 0.91),
            
            # TRY-CATCH
            "try": ("try {\n    // Try block\n} catch (error) {\n    console.error(error);\n}", 0.93),
            "catch": ("catch (error) {\n    console.error(error);\n}", 0.92),
            
            # ASYNC/AWAIT
            "async ": ("async function() {\n    const result = await asyncOperation();\n    return result;\n}", 0.92),
            "await ": ("await asyncOperation()", 0.93),
            
            # COMMON METHODS
            "console.log": ("console.log()", 0.95),
            "return": ("return result;", 0.92),
        }
    
    # ==================== DEFAULT (Generic) ====================
    
    else:
        suggestions = {
            "function": ("function_name() {\n    // Function body\n}", 0.85),
            "if": ("if (condition) {\n    // Code block\n}", 0.85),
            "for": ("for (i = 0; i < n; i++) {\n    // Loop body\n}", 0.85),
            "while": ("while (condition) {\n    // Loop body\n}", 0.85),
        }
    
    # ==================== PATTERN MATCHING ====================
    
    # Check for exact pattern matches
    for pattern, (suggestion, confidence) in suggestions.items():
        if current_line.endswith(pattern.strip()):
            return {
                "suggestion": suggestion,
                "confidence": confidence
            }
    
    # Check for partial matches (for better UX)
    for pattern, (suggestion, confidence) in suggestions.items():
        if pattern.strip().startswith(current_line.strip()) and len(current_line.strip()) > 2:
            return {
                "suggestion": suggestion,
                "confidence": confidence * 0.8  # Lower confidence for partial matches
            }
    
    # ==================== DEFAULT SUGGESTION ====================
    
    # No match found - return generic suggestion
    return {
        "suggestion": "# Continue coding...",
        "confidence": 0.3
    }
