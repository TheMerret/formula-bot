"""Formula normalization and comparison utilities."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_formula(formula: str) -> str:
    """
    Normalize formula for comparison.
    
    This function standardizes formula notation by:
    1. Removing all whitespace
    2. Converting to lowercase
    3. Standardizing operators (^→**, ×→*, ·→*, ÷→/)
    4. Standardizing superscripts (²→2, ³→3)
    5. Removing common LaTeX commands
    
    Args:
        formula: Raw formula text
        
    Returns:
        Normalized formula string
    """
    if not formula:
        return ""
    
    # Remove all whitespace
    normalized = formula.replace(' ', '').replace('\t', '').replace('\n', '')
    
    # Convert to lowercase
    normalized = normalized.lower()
    
    # Standardize operators
    replacements = {
        '^': '**',
        '×': '*',
        '·': '*',
        '÷': '/',
        '²': '2',
        '³': '3',
        '⁴': '4',
        '⁵': '5',
        '⁶': '6',
        '⁷': '7',
        '⁸': '8',
        '⁹': '9',
        '₀': '0',
        '₁': '1',
        '₂': '2',
        '₃': '3',
        '₄': '4',
        '₅': '5',
        '₆': '6',
        '₇': '7',
        '₈': '8',
        '₉': '9',
    }
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    # Remove common LaTeX commands
    latex_patterns = [
        (r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)'),  # \frac{a}{b} → (a)/(b)
        (r'\\sqrt\{([^}]+)\}', r'sqrt(\1)'),  # \sqrt{x} → sqrt(x)
        (r'\\[a-z]+\{([^}]+)\}', r'\1'),  # Remove other LaTeX commands
        (r'\\[a-z]+', ''),  # Remove LaTeX commands without braces
    ]
    
    for pattern, replacement in latex_patterns:
        normalized = re.sub(pattern, replacement, normalized)
    
    # Standardize Greek letters (common in formulas)
    greek_letters = {
        'α': 'alpha',
        'β': 'beta',
        'γ': 'gamma',
        'δ': 'delta',
        'ε': 'epsilon',
        'θ': 'theta',
        'λ': 'lambda',
        'μ': 'mu',
        'ν': 'nu',
        'π': 'pi',
        'ρ': 'rho',
        'σ': 'sigma',
        'τ': 'tau',
        'φ': 'phi',
        'ω': 'omega',
    }
    
    for greek, latin in greek_letters.items():
        normalized = normalized.replace(greek, latin)
    
    logger.debug(f"Normalized '{formula}' → '{normalized}'")
    return normalized


def calculate_similarity(formula1: str, formula2: str) -> float:
    """
    Calculate similarity between two formulas using Levenshtein distance.
    
    Args:
        formula1: First formula (normalized)
        formula2: Second formula (normalized)
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not formula1 or not formula2:
        return 0.0
    
    if formula1 == formula2:
        return 1.0
    
    # Calculate Levenshtein distance
    distance = levenshtein_distance(formula1, formula2)
    
    # Normalize to 0-1 range
    max_len = max(len(formula1), len(formula2))
    if max_len == 0:
        return 0.0
    
    similarity = 1.0 - (distance / max_len)
    
    logger.debug(f"Similarity between '{formula1}' and '{formula2}': {similarity:.2f}")
    return similarity


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    
    This is the minimum number of single-character edits (insertions,
    deletions, or substitutions) required to change one string into the other.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Levenshtein distance
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def extract_variables(formula: str) -> list[str]:
    """
    Extract variable names from a formula.
    
    Args:
        formula: Formula text
        
    Returns:
        List of unique variable names
    """
    # Find all single letters and Greek letters
    variables = re.findall(r'[a-zA-Z]|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|nu|pi|rho|sigma|tau|phi|omega', formula.lower())
    
    # Remove common function names
    functions = {'sin', 'cos', 'tan', 'log', 'ln', 'exp', 'sqrt', 'abs', 'max', 'min'}
    variables = [v for v in variables if v not in functions]
    
    # Return unique variables
    return list(set(variables))