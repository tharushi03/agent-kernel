"""
PII (Personally Identifiable Information) Guardrails
Responssible AI - Protect user privacy
"""

import re


def redact_names(text):
    """
    Redact names (simple pattern matching)
    Capitalizes first letter followed by lowercase letters
    
    Args:
        text: Text to redact
    
    Returns:
        Text with names redacted
    """
    # Pattern: Capitalized word that looks like a name
    # Avoid common words like It, The, etc.
    name_pattern = r'\b(?:[A-Z][a-z]{2,})\b(?!\s(?:is|was|are|the|a|an|in|on|at|to|for|and|or|but))'
    
    def replace_name(match):
        word = match.group(0)
        # Don't redact if it's a known common word
        common_words = {'The', 'This', 'That', 'These', 'Those', 'What', 'When', 'Where', 'Why', 'How', 'Can', 'Will', 'Would', 'Should', 'Could'}
        if word in common_words:
            return word
        return '[NAME]'
    
    return re.sub(name_pattern, replace_name, text)


def redact_phone_numbers(text):
    """
    Redact phone numbers in various formats
    
    Args:
        text: Text to redact
    
    Returns:
        Text with phone numbers redacted
    """
    # Patterns for phone numbers
    patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # XXX-XXX-XXXX
        r'\b\+?\d{1,3}[-.]?\d{1,14}\b',     # International format
        r'\(\d{3}\)\s*\d{3}[-.]?\d{4}'      # (XXX) XXX-XXXX
    ]
    
    text = text
    for pattern in patterns:
        text = re.sub(pattern, '[PHONE]', text)
    
    return text


def redact_email_addresses(text):
    """
    Redact email addresses
    
    Args:
        text: Text to redact
    
    Returns:
        Text with email addresses redacted
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.sub(email_pattern, '[EMAIL]', text)


def redact_credit_card_numbers(text):
    """
    Redact credit card numbers
    
    Args:
        text: Text to redact
    
    Returns:
        Text with credit card numbers redacted
    """
    # Credit card pattern (16 digits, with optional spaces or hyphens)
    cc_pattern = r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
    return re.sub(cc_pattern, '[CREDIT_CARD]', text)


def redact_ssn(text):
    """
    Redact Social Security Numbers (XXX-XX-XXXX format)
    
    Args:
        text: Text to redact
    
    Returns:
        Text with SSNs redacted
    """
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    return re.sub(ssn_pattern, '[SSN]', text)


def redact_addresses(text):
    """
    Redact street addresses (simple pattern)
    
    Args:
        text: Text to redact
    
    Returns:
        Text with addresses redacted
    """
    # Pattern: number followed by street words
    address_pattern = r'\b\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Way|Court|Ct|Circle|Place|Pl|Park|Parkway|Pkwy)\b'
    return re.sub(address_pattern, '[ADDRESS]', text)


def redact_all_pii(text):
    """
    Apply all PII redaction rules
    
    Args:
        text: Text to redact
    
    Returns:
        Text with all PII redacted
    """
    text = redact_names(text)
    text = redact_phone_numbers(text)
    text = redact_email_addresses(text)
    text = redact_credit_card_numbers(text)
    text = redact_ssn(text)
    text = redact_addresses(text)
    
    return text


def check_for_pii(text):
    """
    Check if text contains PII and return findings
    
    Args:
        text: Text to check
    
    Returns:
        Dictionary with PII detection results
    """
    findings = {
        'has_pii': False,
        'detected_types': [],
        'details': {}
    }
    
    # Check for names
    name_pattern = r'\b(?:[A-Z][a-z]{2,})\b(?!\s(?:is|was|are|the|a|an|in|on|at|to|for|and|or|but))'
    if re.search(name_pattern, text):
        findings['has_pii'] = True
        findings['detected_types'].append('Names')
        findings['details']['names'] = re.findall(name_pattern, text)
    
    # Check for phone numbers
    phone_patterns = [r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', r'\b\+?\d{1,3}[-.]?\d{1,14}\b']
    for pattern in phone_patterns:
        if re.search(pattern, text):
            findings['has_pii'] = True
            if 'Phone Numbers' not in findings['detected_types']:
                findings['detected_types'].append('Phone Numbers')
            findings['details']['phone_numbers'] = re.findall(pattern, text)
    
    # Check for emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_pattern, text):
        findings['has_pii'] = True
        findings['detected_types'].append('Email Addresses')
        findings['details']['emails'] = re.findall(email_pattern, text)
    
    # Check for credit card numbers
    cc_pattern = r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
    if re.search(cc_pattern, text):
        findings['has_pii'] = True
        findings['detected_types'].append('Credit Card Numbers')
        findings['details']['credit_cards_found'] = True
    
    # Check for SSN
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    if re.search(ssn_pattern, text):
        findings['has_pii'] = True
        findings['detected_types'].append('Social Security Numbers')
        findings['details']['ssn_found'] = True
    
    return findings


def format_pii_warning(findings):
    """
    Format PII detection findings as a warning message
    
    Args:
        findings: Dictionary from check_for_pii
    
    Returns:
        Formatted warning message
    """
    if not findings['has_pii']:
        return "✅ No PII detected in this conversation."
    
    warning = "\n⚠️ PRIVACY WARNING - PII DETECTED:\n"
    warning += "=" * 50 + "\n"
    warning += f"Detected types: {', '.join(findings['detected_types'])}\n\n"
    warning += "🔒 RECOMMENDATION:\n"
    warning += "  • Avoid sharing personal information\n"
    warning += "  • Use generic preferences instead\n"
    warning += "  • Example: Say 'around $30,000' instead of exact budget\n"
    warning += "=" * 50 + "\n"
    
    return warning


class PIIGuardian:
    """
    Guardian class to protect user privacy in conversations
    """
    
    def __init__(self, auto_redact=True):
        self.auto_redact = auto_redact
        self.pii_log = []
    
    def process_user_input(self, text):
        """
        Process user input for PII
        
        Args:
            text: User input text
        
        Returns:
            Processed text and PII report
        """
        # Check for PII
        findings = check_for_pii(text)
        
        # Log PII findings
        if findings['has_pii']:
            self.pii_log.append({
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'findings': findings
            })
        
        # Auto-redact if enabled
        if self.auto_redact and findings['has_pii']:
            redacted_text = redact_all_pii(text)
            return {
                'original_has_pii': True,
                'redacted_text': redacted_text,
                'warnings': format_pii_warning(findings),
                'findings': findings
            }
        
        return {
            'original_has_pii': findings['has_pii'],
            'redacted_text': text,
            'warnings': format_pii_warning(findings) if findings['has_pii'] else "",
            'findings': findings
        }
    
    def get_pii_report(self):
        """Get summary of PII detections"""
        if not self.pii_log:
            return "📊 No PII detected so far."
        
        report = f"\n📊 PII DETECTION REPORT ({len(self.pii_log)} incidents)\n"
        report += "=" * 50 + "\n"
        
        for i, log in enumerate(self.pii_log[-5:], 1):  # Show last 5
            types = ', '.join(log['findings']['detected_types'])
            report += f"{i}. {log['timestamp']}: {types}\n"
        
        report += "=" * 50 + "\n"
        return report
