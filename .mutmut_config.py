"""
Mutmut Configuration for PokerTool

Mutation testing configuration to identify weak test coverage.
Focuses on critical core modules with high mutation score targets.
"""


def pre_mutation(context):
    """
    Hook called before each mutation.
    Can be used to skip certain mutations or add custom logic.
    """
    # Skip mutations in test files themselves
    if 'test_' in context.filename or '/tests/' in context.filename:
        context.skip = True


# Paths to include for mutation testing (relative to project root)
paths_to_mutate = [
    'src/pokertool/core.py',
    'src/pokertool/database.py',
    'src/pokertool/equity_calculator.py',
    'src/pokertool/gto_calculator.py',
    'src/pokertool/rbac.py',
    'src/pokertool/input_validator.py',
]

# Paths to exclude
paths_to_exclude = [
    'src/pokertool/api.py',  # Too large, test separately
    'src/pokertool/modules/',  # Screen scraping, harder to test
    'scripts/',
    'tests/',
    'pokertool-frontend/',
]

# Runner command (pytest with coverage)
runner = 'python -m pytest -x --tb=short'

# Tests directory
tests_dir = 'tests/'

# Backup directory for original files
backup_dir = '.mutmut_cache'

# Dictionary for custom mutation operators (optional)
dict_synonyms = {
    'True': 'False',
    'False': 'True',
    '==': '!=',
    '!=': '==',
    '<': '>=',
    '<=': '>',
    '>': '<=',
    '>=': '<',
    'and': 'or',
    'or': 'and',
    'in': 'not in',
    'not in': 'in',
    'is': 'is not',
    'is not': 'is',
}
