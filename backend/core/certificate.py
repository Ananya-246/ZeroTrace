"""
Certificate Module
Handles generation of deletion certificates and cryptographic verification
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from utils.logging import Logger


class CertificateManager:
    """Manages deletion certificates and cryptographic verification"""
    
    def __init__(self):
        """Initialize certificate manager"""
        self.logger = Logger()
        self.private_key = None
        self.certificate = None
        self._initialize_keys()
    
    def _initialize_keys(self):
        """Initialize RSA key pair for signing"""
        try:
            # Generate RSA private key
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Generate self-signed certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Secure Wipe Tool"),
                x509.NameAttribute(NameOID.COMMON_NAME, "Deletion Certificate Authority"),
            ])
            
            self.certificate = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                self.private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + datetime.timedelta(days=3650)  # 10 years
            ).sign(self.private_key, hashes.SHA256(), default_backend())
            
            self.logger.log_info("Cryptographic keys initialized")
            
        except Exception as e:
            self.logger.log_error(f"Error initializing keys: {e}")
    
    def verify_usb_authenticity(self) -> bool:
        """
        Verify USB device authenticity
        
        In a production environment, this would check:
        - Hardware signatures
        - Trusted boot chain
        - Secure element verification
        
        Returns:
            True if USB is authentic
        """
        # Placeholder for USB verification logic
        # In production, implement actual hardware verification
        self.logger.log_info("USB authenticity verification (placeholder)")
        return True
    
    def generate_wipe_certificate(self, operation_results: Dict[str, any],
                                 output_path: Optional[str] = None) -> str:
        """
        Generate a deletion certificate for compliance
        
        Args:
            operation_results: Results from wiping operation
            output_path: Optional path to save certificate
        
        Returns:
            Path to certificate file
        """
        try:
            # Create certificate data
            cert_data = {
                'certificate_id': self._generate_certificate_id(),
                'timestamp': datetime.now().isoformat(),
                'operation': {
                    'method': operation_results.get('method', 'unknown'),
                    'start_time': operation_results.get('start_time'),
                    'end_time': operation_results.get('end_time'),
                    'duration': operation_results.get('duration')
                },
                'results': {
                    'total_files': operation_results.get('total_files', 0),
                    'successful': operation_results.get('successful', 0),
                    'failed': operation_results.get('failed', 0)
                },
                'compliance': {
                    'standard': 'NIST SP 800-88',
                    'method_description': self._get_method_description(
                        operation_results.get('method', 'clear')
                    )
                },
                'files': []
            }
            
            # Add file details (limit to prevent huge certificates)
            files = operation_results.get('files', [])
            for file_result in files[:1000]:  # Limit to 1000 files
                cert_data['files'].append({
                    'path': file_result.get('file', 'unknown'),
                    'success': file_result.get('success', False),
                    'verified': file_result.get('verified', False)
                })
            
            # Sign the certificate
            signature = self.sign_deletion_log(cert_data)
            cert_data['signature'] = signature
            cert_data['public_key'] = self._get_public_key_pem()
            
            # Save certificate
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f'deletion_certificate_{timestamp}.json'
            
            with open(output_path, 'w') as f:
                json.dump(cert_data, f, indent=2)
            
            self.logger.log_info(f"Deletion certificate generated: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.log_error(f"Error generating certificate: {e}")
            raise
    
    def sign_deletion_log(self, data: Dict) -> str:
        """
        Cryptographically sign deletion log
        
        Args:
            data: Data to sign
        
        Returns:
            Hex-encoded signature
        """
        try:
            if not self.private_key:
                raise ValueError("Private key not initialized")
            
            # Convert data to JSON string
            data_str = json.dumps(data, sort_keys=True)
            data_bytes = data_str.encode('utf-8')
            
            # Sign with RSA
            signature = self.private_key.sign(
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return signature.hex()
            
        except Exception as e:
            self.logger.log_error(f"Error signing data: {e}")
            return ""
    
    def verify_certificate(self, cert_path: str) -> bool:
        """
        Verify a deletion certificate
        
        Args:
            cert_path: Path to certificate file
        
        Returns:
            True if certificate is valid
        """
        try:
            with open(cert_path, 'r') as f:
                cert_data = json.load(f)
            
            # Extract signature and public key
            signature = bytes.fromhex(cert_data.pop('signature', ''))
            public_key_pem = cert_data.pop('public_key', '')
            
            if not signature or not public_key_pem:
                self.logger.log_error("Certificate missing signature or public key")
                return False
            
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # Verify signature
            data_str = json.dumps(cert_data, sort_keys=True)
            data_bytes = data_str.encode('utf-8')
            
            try:
                public_key.verify(
                    signature,
                    data_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                self.logger.log_info(f"Certificate verified: {cert_path}")
                return True
            except Exception:
                self.logger.log_error(f"Certificate signature invalid: {cert_path}")
                return False
            
        except Exception as e:
            self.logger.log_error(f"Error verifying certificate: {e}")
            return False
    
    def _generate_certificate_id(self) -> str:
        """Generate unique certificate ID"""
        timestamp = datetime.now().isoformat()
        hash_obj = hashlib.sha256(timestamp.encode())
        return hash_obj.hexdigest()[:16].upper()
    
    def _get_method_description(self, method: str) -> str:
        """Get description of wiping method"""
        descriptions = {
            'clear': 'NIST Clear - Single pass overwrite with zeros',
            'purge': 'NIST Purge - Multi-pass overwrite (DoD 5220.22-M)'
        }
        return descriptions.get(method, 'Unknown method')
    
    def _get_public_key_pem(self) -> str:
        """Get public key in PEM format"""
        if not self.certificate:
            return ""
        
        public_key = self.certificate.public_key()
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def export_certificate_as_pdf(self, cert_path: str, pdf_path: str) -> bool:
        """
        Export certificate as PDF for compliance
        
        Args:
            cert_path: Path to JSON certificate
            pdf_path: Path for output PDF
        
        Returns:
            True if successful
        """
        try:
            # This would require a PDF library like reportlab
            # Placeholder implementation
            self.logger.log_warning("PDF export not implemented")
            return False
        except Exception as e:
            self.logger.log_error(f"Error exporting PDF: {e}")
            return False
    
    def save_keys(self, key_dir: str = 'certificates'):
        """
        Save private key and certificate to files
        
        Args:
            key_dir: Directory to save keys
        """
        try:
            key_path = Path(key_dir)
            key_path.mkdir(exist_ok=True)
            
            # Save private key
            private_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            with open(key_path / 'private_key.pem', 'wb') as f:
                f.write(private_pem)
            
            # Save certificate
            cert_pem = self.certificate.public_bytes(serialization.Encoding.PEM)
            
            with open(key_path / 'certificate.pem', 'wb') as f:
                f.write(cert_pem)
            
            self.logger.log_info(f"Keys saved to {key_dir}")
            
        except Exception as e:
            self.logger.log_error(f"Error saving keys: {e}")