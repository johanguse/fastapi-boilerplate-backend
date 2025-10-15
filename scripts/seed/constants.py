"""Constants and configuration for seed data."""

import random

# Password for all seed users
DEFAULT_PASSWORD = 'admin123'

# Diverse user agents for realistic activity logs
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
]

# Diverse IP addresses (for demo purposes - using documentation IPs)
IP_ADDRESSES = [
    '192.168.1.100',
    '10.0.0.50',
    '172.16.0.25',
    '203.0.113.45',  # Documentation IP
    '198.51.100.78',  # Documentation IP
    '192.0.2.123',  # Documentation IP
    '2001:db8::1',  # IPv6 documentation
    '127.0.0.1',
]


def random_ip():
    """Get a random IP address."""
    return random.choice(IP_ADDRESSES)


def random_user_agent():
    """Get a random user agent."""
    return random.choice(USER_AGENTS)
