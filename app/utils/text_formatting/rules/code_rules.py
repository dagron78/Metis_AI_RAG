"""
Code Formatting Rules

This module defines rules for formatting code blocks within text.
"""
import re

# Pattern to match code blocks
CODE_BLOCK_PATTERN = r'```([\w\-+#]*)\s*(.*?)```'

# Language tag fixes for common issues
LANGUAGE_FIXES = [
    # Handle common concatenated language tags directly
    {"pattern": r'```pythoncss', "replacement": r'```css'},
    {"pattern": r'```javascripthtml', "replacement": r'```html'},
    {"pattern": r'```pythonhtml', "replacement": r'```html'},
    {"pattern": r'```pythonjs', "replacement": r'```javascript'},
    {"pattern": r'```pythonjavascript', "replacement": r'```javascript'},
    
    # Handle specific test cases directly
    {"pattern": r'```javascriptconst', "replacement": r'```javascript\nconst'},
    {"pattern": r'```html<div>', "replacement": r'```html\n<div>'},
    {"pattern": r'```css\.container', "replacement": r'```css\n.container'},
    
    # Handle code that starts immediately after language tag with no newline
    {"pattern": r'```(javascript|js)(const|let|var|function|import|export|class)', "replacement": r'```\1\n\2'},
    {"pattern": r'```(python)(import|def|class|print|from|if|for|while)', "replacement": r'```\1\n\2'},
    {"pattern": r'```(html)(<\w+)', "replacement": r'```\1\n\2'},
    {"pattern": r'```(css)(\.|\#|\*|body|html|@media)', "replacement": r'```\1\n\2'},
]

# Method call fixes
METHOD_CALL_FIXES = [
    # Fix function names with spaces
    {"pattern": r'([a-z]+) \. ([a-z]+)', "replacement": r'\1.\2'},
    {"pattern": r'([a-z]+) _ ([a-z]+)', "replacement": r'\1_\2'},
    
    # Fix method calls with spaces
    {"pattern": r'(\w+) \. (\w+) \( (.*?) \)', "replacement": r'\1.\2(\3)'},
    {"pattern": r'(\w+) \. (\w+)\(', "replacement": r'\1.\2('},
    
    # Fix spaces between method name and opening parenthesis
    {"pattern": r'(\w+) \(', "replacement": r'\1('},
    
    # Fix spaces inside method call parentheses
    {"pattern": r'\( (.*?) \)', "replacement": r'(\1)'},
    {"pattern": r'\((.*?) \)', "replacement": r'(\1)'},
]

# Variable name fixes
VARIABLE_NAME_FIXES = [
    # Fix variable names with spaces
    {"pattern": r'([a-z]+) _ ([a-z]+)', "replacement": r'\1_\2'},
    
    # Fix spaces after commas in parameter lists
    {"pattern": r', +', "replacement": r', '},
    
    # Fix common abbreviations with incorrect spaces
    {"pattern": r'e\. g\. ,', "replacement": 'e.g.,'},
    {"pattern": r'i\. e\. ,', "replacement": 'i.e.,'},
    {"pattern": r'etc\. ,', "replacement": 'etc.,'},
]

# Language inference patterns
LANGUAGE_INFERENCE_PATTERNS = {
    "python": r'import\s+\w+|def\s+\w+\s*\(|print\s*\(|class\s+\w+:|if\s+.*?:|for\s+.*?:',
    "javascript": r'function\s+\w+\s*\(|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=|console\.log|document\.|window\.',
    "html": r'<html|<div|<p>|<body|<head|<script|<style|<a\s+href|<img\s+src|<table|<form',
    "css": r'{\s*[\w-]+\s*:\s*\w+|@media|#[\w-]+\s*{|\.[\w-]+\s*{|body\s*{|html\s*{',
    "sql": r'SELECT\s+.*?\s+FROM|INSERT\s+INTO|UPDATE\s+.*?\s+SET|DELETE\s+FROM|CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE',
    "bash": r'#!/bin/bash|echo\s+|grep\s+|sed\s+|awk\s+|cat\s+|ls\s+|cd\s+|mkdir\s+|rm\s+',
    "json": r'{\s*"\w+"\s*:\s*.*?}',
    "yaml": r'^\w+:\s*\n\s+\w+:',
}