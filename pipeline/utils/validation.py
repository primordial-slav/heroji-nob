"""
Field validation for extracted soldier data.

Validates extracted fields and adds issues when validation fails.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class FieldValidator:
    """
    Validates extracted soldier fields and tracks validation issues.

    Validation rules:
        - birth_year: 4 digits, range 1880-1935
        - death_date: valid format, year 1941-1945
        - death_cause: recognized values
        - age at death: 14-70 years
        - high confidence requires name

    Usage:
        validator = FieldValidator()
        soldier = validator.validate(soldier_data)
        # soldier now has updated parsing_issues and possibly downgraded confidence
    """

    # Valid death causes (lowercase for comparison)
    VALID_DEATH_CAUSES = {
        'poginuo', 'poginula',
        'umro', 'umrla',
        'nestao', 'nestala',
        'streljan', 'streljana',
        'ubijen', 'ubijena',
        'zarobljen', 'zarobljena',
        'ranjen', 'ranjena',
        'obešen', 'obešena',
        'unknown', 'nepoznato',
        '',  # Allow empty
    }

    # Date patterns
    DATE_PATTERNS = [
        r'^\d{4}$',  # Just year: 1943
        r'^\d{1,2}\.\d{1,2}\.\d{4}$',  # DD.MM.YYYY or D.M.YYYY
        r'^\d{1,2}\.\s*\w+\s*\d{4}$',  # DD. month YYYY
        r'^\w+\s*\d{4}$',  # month YYYY
        r'^\d{4}-\d{2}-\d{2}$',  # ISO format
    ]

    def __init__(self, logger: logging.Logger = None):
        """Initialize validator with optional logger."""
        self.logger = logger or logging.getLogger(__name__)
        self.stats = {
            'validated': 0,
            'issues_added': 0,
            'confidence_downgraded': 0,
        }

    def validate(self, soldier: Dict) -> Dict:
        """
        Validate soldier fields and add issues.

        Args:
            soldier: Dict with extracted soldier data

        Returns:
            Updated soldier dict with validation issues added
        """
        issues = []
        original_confidence = soldier.get('confidence', 'medium')

        # Get existing issues
        existing_issues = soldier.get('parsing_issues', [])
        if isinstance(existing_issues, str):
            existing_issues = [i.strip() for i in existing_issues.split(',') if i.strip()]

        # Validate birth year
        birth_issue = self._validate_birth_year(soldier.get('birth_year', ''))
        if birth_issue:
            issues.append(birth_issue)

        # Validate death date
        death_issue = self._validate_death_date(soldier.get('death_date', ''))
        if death_issue:
            issues.append(death_issue)

        # Validate death cause
        cause_issue = self._validate_death_cause(soldier.get('death_cause', ''))
        if cause_issue:
            issues.append(cause_issue)

        # Validate age at death
        age_issue = self._validate_age_at_death(
            soldier.get('birth_year', ''),
            soldier.get('death_date', '')
        )
        if age_issue:
            issues.append(age_issue)

        # Check name requirement for high confidence
        new_confidence = original_confidence
        if original_confidence == 'high':
            if not soldier.get('last_name') or not soldier.get('first_name'):
                issues.append('high confidence but missing name')
                new_confidence = 'medium'
                self.stats['confidence_downgraded'] += 1

        # Merge issues
        all_issues = existing_issues + issues
        soldier['parsing_issues'] = all_issues
        soldier['confidence'] = new_confidence

        # Update stats
        self.stats['validated'] += 1
        self.stats['issues_added'] += len(issues)

        if issues:
            self.logger.debug(
                f"Validation issues for {soldier.get('last_name', '?')}: {issues}"
            )

        return soldier

    def _validate_birth_year(self, birth_year: str) -> Optional[str]:
        """Validate birth year is 4 digits in range 1880-1935."""
        if not birth_year:
            return None

        # Clean input
        birth_year = str(birth_year).strip()

        # Must be 4 digits
        if not re.match(r'^\d{4}$', birth_year):
            return f'invalid birth year format: {birth_year}'

        year = int(birth_year)
        if not (1880 <= year <= 1935):
            return f'birth year {year} outside range 1880-1935'

        return None

    def _validate_death_date(self, death_date: str) -> Optional[str]:
        """Validate death date format and year range 1941-1945."""
        if not death_date:
            return None

        death_date = str(death_date).strip()

        # Check format matches one of our patterns
        format_valid = any(
            re.match(pattern, death_date)
            for pattern in self.DATE_PATTERNS
        )

        if not format_valid:
            return f'invalid death date format: {death_date}'

        # Extract year
        year_match = re.search(r'(\d{4})', death_date)
        if year_match:
            year = int(year_match.group(1))
            if not (1941 <= year <= 1945):
                return f'death year {year} outside range 1941-1945'

        return None

    def _validate_death_cause(self, death_cause: str) -> Optional[str]:
        """Validate death cause is a recognized value."""
        if not death_cause:
            return None

        cause_lower = death_cause.lower().strip()

        # Check exact match or if cause contains a valid value
        if cause_lower in self.VALID_DEATH_CAUSES:
            return None

        # Check if any valid cause is contained in the value
        for valid_cause in self.VALID_DEATH_CAUSES:
            if valid_cause and valid_cause in cause_lower:
                return None

        return f'unrecognized death cause: {death_cause}'

    def _validate_age_at_death(
        self,
        birth_year: str,
        death_date: str
    ) -> Optional[str]:
        """Validate age at death is 14-70 years."""
        if not birth_year or not death_date:
            return None

        try:
            birth = int(str(birth_year).strip())
        except ValueError:
            return None  # Already caught by birth year validation

        # Extract death year
        year_match = re.search(r'(\d{4})', str(death_date))
        if not year_match:
            return None  # Already caught by death date validation

        death = int(year_match.group(1))
        age = death - birth

        if not (14 <= age <= 70):
            return f'unlikely age at death: {age} years'

        return None

    def get_stats(self) -> Dict[str, int]:
        """Get validation statistics."""
        return dict(self.stats)

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self.stats = {
            'validated': 0,
            'issues_added': 0,
            'confidence_downgraded': 0,
        }
