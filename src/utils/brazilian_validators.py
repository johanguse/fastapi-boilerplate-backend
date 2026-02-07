"""Brazilian document validators and formatters (CPF, CNPJ, CEP)."""


def validate_cpf(cpf: str) -> bool:
    """
    Validate CPF (Cadastro de Pessoas Físicas).
    11 digits: XXX.XXX.XXX-XX
    """
    # Remove non-digits
    clean_cpf = ''.join(filter(str.isdigit, cpf))

    # Must be 11 digits
    if len(clean_cpf) != 11:
        return False

    # Check for known invalid patterns (all same digits)
    if len(set(clean_cpf)) == 1:
        return False

    # Validate first check digit
    sum_val = 0
    for i in range(9):
        sum_val += int(clean_cpf[i]) * (10 - i)
    remainder = (sum_val * 10) % 11
    if remainder in (10, 11):
        remainder = 0
    if remainder != int(clean_cpf[9]):
        return False

    # Validate second check digit
    sum_val = 0
    for i in range(10):
        sum_val += int(clean_cpf[i]) * (11 - i)
    remainder = (sum_val * 10) % 11
    if remainder in (10, 11):
        remainder = 0
    if remainder != int(clean_cpf[10]):
        return False

    return True


def validate_cnpj(cnpj: str) -> bool:
    """
    Validate CNPJ (Cadastro Nacional da Pessoa Jurídica).
    14 digits: XX.XXX.XXX/XXXX-XX
    """
    # Remove non-digits
    clean_cnpj = ''.join(filter(str.isdigit, cnpj))

    # Must be 14 digits
    if len(clean_cnpj) != 14:
        return False

    # Check for known invalid patterns (all same digits)
    if len(set(clean_cnpj)) == 1:
        return False

    # Validate first check digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_val = 0
    for i in range(12):
        sum_val += int(clean_cnpj[i]) * weights1[i]
    remainder = sum_val % 11
    digit1 = 0 if remainder < 2 else 11 - remainder
    if digit1 != int(clean_cnpj[12]):
        return False

    # Validate second check digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_val = 0
    for i in range(13):
        sum_val += int(clean_cnpj[i]) * weights2[i]
    remainder = sum_val % 11
    digit2 = 0 if remainder < 2 else 11 - remainder
    if digit2 != int(clean_cnpj[13]):
        return False

    return True


def validate_cpf_or_cnpj(document: str) -> dict:
    """
    Validate CPF or CNPJ based on length.
    Returns: { valid: bool, type: 'cpf' | 'cnpj' | 'unknown', message?: str }
    """
    clean_doc = ''.join(filter(str.isdigit, document))

    if len(clean_doc) == 11:
        valid = validate_cpf(clean_doc)
        return {
            'valid': valid,
            'type': 'cpf',
            'message': None if valid else 'CPF inválido',
        }

    if len(clean_doc) == 14:
        valid = validate_cnpj(clean_doc)
        return {
            'valid': valid,
            'type': 'cnpj',
            'message': None if valid else 'CNPJ inválido',
        }

    return {
        'valid': False,
        'type': 'unknown',
        'message': 'Digite um CPF (11 dígitos) ou CNPJ (14 dígitos) válido',
    }


def format_cpf(cpf: str) -> str:
    """Format CPF: XXX.XXX.XXX-XX"""
    clean = ''.join(filter(str.isdigit, cpf))[:11]
    if len(clean) <= 3:
        return clean
    if len(clean) <= 6:
        return f'{clean[:3]}.{clean[3:]}'
    if len(clean) <= 9:
        return f'{clean[:3]}.{clean[3:6]}.{clean[6:]}'
    return f'{clean[:3]}.{clean[3:6]}.{clean[6:9]}-{clean[9:]}'


def format_cnpj(cnpj: str) -> str:
    """Format CNPJ: XX.XXX.XXX/XXXX-XX"""
    clean = ''.join(filter(str.isdigit, cnpj))[:14]
    if len(clean) <= 2:
        return clean
    if len(clean) <= 5:
        return f'{clean[:2]}.{clean[2:]}'
    if len(clean) <= 8:
        return f'{clean[:2]}.{clean[2:5]}.{clean[5:]}'
    if len(clean) <= 12:
        return f'{clean[:2]}.{clean[2:5]}.{clean[5:8]}/{clean[8:]}'
    return f'{clean[:2]}.{clean[2:5]}.{clean[5:8]}/{clean[8:12]}-{clean[12:]}'


def format_cpf_or_cnpj(document: str) -> str:
    """Format CPF or CNPJ based on length"""
    clean = ''.join(filter(str.isdigit, document))
    if len(clean) <= 11:
        return format_cpf(clean)
    return format_cnpj(clean)


def format_cep(cep: str) -> str:
    """Format CEP: XXXXX-XXX"""
    clean = ''.join(filter(str.isdigit, cep))[:8]
    if len(clean) <= 5:
        return clean
    return f'{clean[:5]}-{clean[5:]}'


# Brazilian states list
BRAZILIAN_STATES = [
    {'code': 'AC', 'name': 'Acre'},
    {'code': 'AL', 'name': 'Alagoas'},
    {'code': 'AP', 'name': 'Amapá'},
    {'code': 'AM', 'name': 'Amazonas'},
    {'code': 'BA', 'name': 'Bahia'},
    {'code': 'CE', 'name': 'Ceará'},
    {'code': 'DF', 'name': 'Distrito Federal'},
    {'code': 'ES', 'name': 'Espírito Santo'},
    {'code': 'GO', 'name': 'Goiás'},
    {'code': 'MA', 'name': 'Maranhão'},
    {'code': 'MT', 'name': 'Mato Grosso'},
    {'code': 'MS', 'name': 'Mato Grosso do Sul'},
    {'code': 'MG', 'name': 'Minas Gerais'},
    {'code': 'PA', 'name': 'Pará'},
    {'code': 'PB', 'name': 'Paraíba'},
    {'code': 'PR', 'name': 'Paraná'},
    {'code': 'PE', 'name': 'Pernambuco'},
    {'code': 'PI', 'name': 'Piauí'},
    {'code': 'RJ', 'name': 'Rio de Janeiro'},
    {'code': 'RN', 'name': 'Rio Grande do Norte'},
    {'code': 'RS', 'name': 'Rio Grande do Sul'},
    {'code': 'RO', 'name': 'Rondônia'},
    {'code': 'RR', 'name': 'Roraima'},
    {'code': 'SC', 'name': 'Santa Catarina'},
    {'code': 'SP', 'name': 'São Paulo'},
    {'code': 'SE', 'name': 'Sergipe'},
    {'code': 'TO', 'name': 'Tocantins'},
]
