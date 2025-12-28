import sys
import argparse
import json
import re
import random
import os
import urllib.request
from pathlib import Path
from dataclasses import dataclass
from typing import Any

VERSION = "1.2"
UPDATE_URL = ""
BASE_DIR = Path(__file__).resolve().parent

COLOR_LIST: dict[str, set[str]] = {
    "en": {"yellow", "red", "green", "blue", "white", "black", "purple", "cyan", "orange", "gray"},
    "es": {"amarillo", "rojo", "verde", "azul", "blanco", "negro", "morado", "cian", "naranja", "gris"},
    "de": {"gelb", "rot", "grün", "blau", "weiss", "schwarz", "lila", "cyan", "orange", "grau"},
    "pt": {"amarelo", "vermelho", "verde", "azul", "branco", "preto", "roxo", "ciano", "laranja", "cinza"},
    "ru": {"zheltyy", "krasnyy", "zelenyy", "siniy", "belyy", "chernyy", "fioletovyy", "goluboy", "oranzhevyy", "seryy"}
}

@dataclass
class ProgrammingProfile:
    id: str
    name: str
    flags: list[str]
    prefix: str
    suffix: str
    theme_rgb: tuple[int, int, int]
    
    def format(self, code: str) -> str:
        return f"{self.prefix}{code}{self.suffix}"
        
    def get_theme_ansi(self) -> str:
        r, g, b = self.theme_rgb
        return f"\033[38;2;{r};{g};{b}m"

TARGET_PROFILES = {
    'python': ProgrammingProfile('python', "Python", ['-p', '--python'], "\\033[", "m", (55, 118, 171)),
    'java':   ProgrammingProfile('java', "Java", ['-j', '--java'], "\\u001b[", "m", (220, 20, 60)),
    'cpp':    ProgrammingProfile('cpp', "C++", ['-c', '--cpp'], "\\x1b[", "m", (138, 43, 226)),
    'js':     ProgrammingProfile('js', "JavaScript", ['-s', '--js'], "\\u001b[", "m", (247, 223, 30)),
    'bash':   ProgrammingProfile('bash', "Bash", ['-b', '--bash'], "\\e[", "m", (78, 154, 6)),
    'ruby':   ProgrammingProfile('ruby', "Ruby", ['-rb', '--ruby'], "\\e[", "m", (204, 52, 45)), 
    'go':     ProgrammingProfile('go', "Go", ['-g', '--go'], "\\x1b[", "m", (0, 173, 216))
}

class SystemManager:
    def __init__(self):
        self.colors: dict[str, str] = {}
        self.strings: dict[str, str] = {} 
        self.current_pack = 'en'
        self.config_path = BASE_DIR / 'assets' / 'settings.json'
        
        self.defaults = {
            "color_mode": "{0} Color Mode",
            "prompt": ">>",
            "warning": "[!] Warning: '{0}' is not a valid color.",
            "download_hint": "Color key not available, you can download a variety of colors at: {0}",
            "missing_pack_msg": "[!] Detected input from '{0}'. The file pack 'pack_{1}.json' is missing.\n    Download it here: {2}",
            "exit_msg": "Exiting...",
            "pack_error": "[!] Error loading file pack: {0}",
            "help_col_flag": "FLAG",
            "help_col_pack": "PACK",
            "help_col_option": "OPTION",
            "help_col_desc": "DESCRIPTION",
            "help_msg_avail_pack": "available interface pack: {0}",
            "help_msg_no_pack": "You don't have any pack at the moment",
            "help_msg_input_desc": "Hex Codes or Color Names",
            "help_msg_random_desc": "Generate N random colors",
            "security_limit_msg": "[!] Security: Limit of {0} colors exceeded. Truncating to {0}.",
            "help_check_update": "Check and update CGen",
            "help_show_version": "Show current version",
            "help_gen_profile": "Generate for {0}",
            "msg_checking_updates": "[i] Checking for updates from GitHub...",
            "msg_new_version": "[!] New version found: {0} (Current: {1})",
            "msg_update_prompt": "[?] Do you want to download and install this update? [y/N] ",
            "msg_updating": "[!] Updating...",
            "msg_update_success": "[OK] Update successful! Please restart CGen.",
            "msg_write_error": "[!] Error writing file: {0}",
            "msg_latest_version": "[OK] You are using the latest version ({0}).",
            "msg_ver_verify_error": "[!] Could not verify remote version string.",
            "msg_fetch_error": "[!] Failed to fetch update. Status Code: {0}",
            "msg_update_check_fail": "[!] Update check failed: {0}",
            "msg_pack_fallback": "[!] pack '{0}' not found. Falling back to 'en'.",
            "err_general": "[!] Error: {0}"
        }
        
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        base_settings = {
            "pack": "en",
            "language": "python",
            "random-limit": 100,
            "check-update": True
        }
        
        if not self.config_path.exists():
            self._save_config_file(base_settings)
            return base_settings

        try:
            with self.config_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return base_settings

    def _save_config_file(self, data: dict[str, Any]):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with self.config_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def save_pack(self, pack_code: str):
        self.config['pack'] = pack_code
        self._save_config_file(self.config)

    def save_profile(self, profile_id: str):
        self.config['language'] = profile_id
        self._save_config_file(self.config)

    def save_random_limit(self, limit: int):
        self.config['random-limit'] = limit
        self._save_config_file(self.config)

    def get_config_val(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, self.defaults.get(key, default))

    def get_available_packs(self) -> list[str]:
        pack_dir = BASE_DIR / 'assets'
        if not pack_dir.exists():
            return []
        
        codes = [f.stem.replace('pack_', '') for f in pack_dir.glob('pack_*.json') if f.is_file()]
        return sorted(codes)

    def load_pack(self, pack_code: str):
        self.current_pack = pack_code
        file_path = BASE_DIR / 'assets' / f'pack_{pack_code}.json'
        
        if not file_path.exists():
            if pack_code != 'en':
                print(f"\033[93m{self.get_text('msg_pack_fallback', pack_code)}\033[0m")
                self.load_pack('en')
            return

        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                self.colors = data.get('palette', {})
                self.strings = data.get('interface', {})
        except Exception as e:
            print(f"\033[91m{self.defaults['pack_error'].format(e)}\033[0m")

    def get_text(self, key: str, *args) -> str:
        template = self.strings.get(key, self.defaults.get(key, key))
        if args:
            return template.format(*args)
        return template

    def resolve_color(self, name_or_hex: str) -> tuple[str, tuple[int, int, int]] | None:
        clean = name_or_hex.strip().lower()
        
        if clean in self.colors:
            hex_val = self.colors[clean]
            return (hex_val, self._hex_to_rgb(hex_val))
            
        hex_match = re.match(r'^#?([a-f0-9]{6}|[a-f0-9]{3})$', clean)
        if hex_match:
            hex_part = hex_match.group(1)
            if len(hex_part) == 3:
                hex_part = "".join(c * 2 for c in hex_part)
                
            final_hex = f"#{hex_part}" 
            try:
                return (final_hex, self._hex_to_rgb(final_hex))
            except ValueError:
                pass
        return None

    def detect_potential_pack(self, user_input: str) -> str | None:
        clean = user_input.strip().lower()
        for pack, words in COLOR_LIST.items():
            if clean in words:
                return pack
        return None

    def is_file_pack_present(self, pack_code: str) -> bool:
        return (BASE_DIR / 'assets' / f'pack_{pack_code}.json').exists()

    @staticmethod
    def _hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
        hex_code = hex_code.lstrip('#')
        if len(hex_code) == 3:
            hex_code = "".join(c * 2 for c in hex_code)
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

SYSTEM = SystemManager()

def print_aesthetic_help():
    reset = "\033[0m"
    turquoise = "\033[1;36m" 
    gray = "\033[90m"
    bold = "\033[1m"
    
    print(f"\n{turquoise}   CGen v{VERSION} {reset}")
    print(f"   {gray}{'='*38}{reset}\n")

    col_flag = SYSTEM.get_text('help_col_flag')
    col_pack = SYSTEM.get_text('help_col_pack')
    print(f"   {bold}{col_flag:<18} {col_pack:<15}{reset}")
    print(f"   {gray}{'-'*18} {'-'*15}{reset}")

    for _, profile in TARGET_PROFILES.items():
        flags_desc = ", ".join(profile.flags)
        theme = profile.get_theme_ansi()
        print(f"   {flags_desc:<18} {theme}{profile.name}{reset}")

    col_opt = SYSTEM.get_text('help_col_option')
    col_desc = SYSTEM.get_text('help_col_desc')
    print(f"\n   {bold}{col_opt:<18} {col_desc:<15}{reset}")
    print(f"   {gray}{'-'*18} {'-'*15}{reset}")

    packs = SYSTEM.get_available_packs()
    if packs:
        pack_str = ", ".join(packs)
        pack_desc = SYSTEM.get_text('help_msg_avail_pack', pack_str)
    else:
        pack_desc = SYSTEM.get_text('help_msg_no_pack')

    print(f"   {'--pack <code>':<18} {pack_desc}")
    
    rand_desc = SYSTEM.get_text('help_msg_random_desc')
    print(f"   {'-r, --random [N]':<18} {rand_desc}")

    print(f"   {'--update':<18} {SYSTEM.get_text('help_check_update')}")
    print(f"   {'--version':<18} {SYSTEM.get_text('help_show_version')}")
    
    input_desc = SYSTEM.get_text('help_msg_input_desc')
    print(f"   {'inputs...':<18} {input_desc}")
    print("\n")

class AestheticParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"\n\033[91m{SYSTEM.get_text('err_general', message)}\033[0m")
        print_aesthetic_help()
        sys.exit(2)

    def print_help(self, file=None):
        print_aesthetic_help()

class AnsiFactory:
    def __init__(self, profile: ProgrammingProfile):
        self.profile = profile

    def generate(self, rgb: tuple[int, int, int]) -> str:
        r, g, b = rgb
        code_body = f"38;2;{r};{g};{b}"
        return self.profile.format(code_body)

    def get_preview_str(self, rgb: tuple[int, int, int]) -> str:
        r, g, b = rgb
        return f"\033[38;2;{r};{g};{b}m"

def print_result_line(idx: int, profile_name: str, disp_name: str, code_inner: str, preview_block: str, label_padding: int, theme_ansi: str):
    white = "\033[97m"
    reset = "\033[0m"
    
    visible_label = f"{profile_name} ({disp_name})"
    visible_code = f'"{code_inner}"'
    
    total_pad = max(0, label_padding - len(visible_label))
    pad_left = total_pad // 2
    pad_right = total_pad - pad_left
    
    str_pad_left = " " * pad_left
    str_pad_right = " " * pad_right
    
    code_pad_len = max(0, 30 - len(visible_code))
    code_pad_str = " " * code_pad_len
    
    idx_str = f"{white}{idx:>4}:{reset}"
    prof_str = f"{theme_ansi}{profile_name}{reset}"
    hex_str = f"{theme_ansi}({reset}{white}{disp_name}{reset}{theme_ansi}){reset}"
    eq_str = f"{theme_ansi}={reset}"
    code_str = f'{theme_ansi}"{reset}{white}{code_inner}{reset}{theme_ansi}"{reset}'
    
    print(f"{idx_str} {prof_str} {hex_str}{str_pad_left} {eq_str} {str_pad_right}{code_str}{code_pad_str}   {preview_block}")

def get_github_link_msg(pack_code: str) -> str:
    link = f"https://github.com/SparkCry/ColorGenerator/tree/main/assets/pack_{pack_code}.json"
    return SYSTEM.get_text('missing_pack_msg', pack_code.upper(), pack_code, link)

def process_token(token: str, factory: AnsiFactory, reset: str) -> tuple[str, str, str, str] | None:
    res = SYSTEM.resolve_color(token)
    
    if res:
        hex_str, rgb = res
        disp_name = hex_str
        
        code_inner = factory.generate(rgb)
        block = factory.get_preview_str(rgb) + "█████" + reset
        return (factory.profile.name, disp_name, code_inner, block)
    else:
        detected_pack = SYSTEM.detect_potential_pack(token)
        if detected_pack and not SYSTEM.is_file_pack_present(detected_pack):
            msg = get_github_link_msg(detected_pack)
            print(f"\033[93m{msg}\033[0m", file=sys.stderr)
            return None
            
        warn_msg = SYSTEM.get_text('warning', token)
        print(f"\033[93m{warn_msg}\033[0m", file=sys.stderr)
        return None

def check_for_updates(silent=False, manual_request=False):
    if not silent:
        print(f"\033[96m{SYSTEM.get_text('msg_checking_updates')}\033[0m")
    
    try:
        timeout = 3 if silent else 10
        with urllib.request.urlopen(UPDATE_URL, timeout=timeout) as response:
            if response.status == 200:
                new_code = response.read().decode('utf-8')
                
                ver_match = re.search(r'VERSION\s*=\s*"([^"]+)"', new_code)
                if ver_match:
                    new_ver = ver_match.group(1)
                    if new_ver != VERSION:
                        print(f"\033[92m{SYSTEM.get_text('msg_new_version', new_ver, VERSION)}\033[0m")
                        
                        try:
                            choice = input(f"\033[93m{SYSTEM.get_text('msg_update_prompt')}\033[0m").strip().lower()
                        except (EOFError, KeyboardInterrupt):
                            choice = 'n'
                        
                        if choice == 'y':
                            print(f"\033[93m{SYSTEM.get_text('msg_updating')}\033[0m")
                            try:
                                with open(__file__, 'w', encoding='utf-8') as f:
                                    f.write(new_code)
                                print(f"\033[92m{SYSTEM.get_text('msg_update_success')}\033[0m")
                                sys.exit(0)
                            except Exception as e:
                                print(f"\033[91m{SYSTEM.get_text('msg_write_error', e)}\033[0m")
                                sys.exit(1)
                        else:
                            if manual_request: sys.exit(0)
                            return 
                    else:
                        if not silent:
                            print(f"\033[92m{SYSTEM.get_text('msg_latest_version', VERSION)}\033[0m")
                            if manual_request: sys.exit(0)
                else:
                    if not silent:
                        print(f"\033[93m{SYSTEM.get_text('msg_ver_verify_error')}\033[0m")
            else:
                if not silent:
                    print(f"\033[91m{SYSTEM.get_text('msg_fetch_error', response.status)}\033[0m")
    except Exception as e:
        if not silent:
            print(f"\033[91m{SYSTEM.get_text('msg_update_check_fail', e)}\033[0m")
    
    if manual_request:
        sys.exit(0)

def interactive_mode(profile: ProgrammingProfile):
    factory = AnsiFactory(profile)
    theme = profile.get_theme_ansi()
    reset = "\033[0m"
    white = "\033[97m"
    
    txt_mode = SYSTEM.get_text('color_mode', profile.name)
    
    print(f"{white}{'='*30}{reset}")
    print(f"{theme}    {txt_mode} {reset}")
    print(f"{white}{'='*30}{reset}" + "\n")
    
    counter = 1
    
    while True:
        try:
            prompt_txt = SYSTEM.get_text('prompt')
            user_input = input(f"{theme}{prompt_txt} {reset}")
            
            print("\033[1A\033[2K", end="")
            sys.stdout.flush() 
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                break
            
            if not user_input.strip():
                continue

            sanitized_input = user_input.replace(',', ' ')
            raw_inputs = sanitized_input.split()

            line_results = [] 
            random_cmd_executed = False
            limit_warning = None 

            i = 0
            while i < len(raw_inputs):
                token = raw_inputs[i]
                
                if token.lower() == 'random':
                    count = 1
                    consumed = 1  
                    
                    if i + 1 < len(raw_inputs) and raw_inputs[i+1].isdigit():
                        count = int(raw_inputs[i+1])
                        consumed += 1 
                    
                    if random_cmd_executed:
                        i += consumed
                        continue

                    random_cmd_executed = True

                    limit = SYSTEM.get_config_val('random-limit', 100)
                    if count > limit:
                        SYSTEM.save_random_limit(limit)
                        limit_warning = SYSTEM.get_text('security_limit_msg', limit)
                        count = limit

                    for _ in range(count):
                        rgb_tuple = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                        hex_str = "#{:02x}{:02x}{:02x}".format(*rgb_tuple)
                        
                        code_inner = factory.generate(rgb_tuple)
                        block = factory.get_preview_str(rgb_tuple) + "█████" + reset
                        line_results.append((profile.name, hex_str, code_inner, block))
                    
                    i += consumed
                    continue

                result = process_token(token, factory, reset)
                if result:
                    line_results.append(result)
                
                i += 1
            
            if line_results:
                lengths = [len(f"{p} ({d})") for p, d, _, _ in line_results]
                current_max_len = max([30] + lengths)
                
                for p_name, d_name, c_inner, blk in line_results:
                    print_result_line(counter, p_name, d_name, c_inner, blk, current_max_len, theme)
                    counter += 1

            if limit_warning:
                print(f"\033[93m{limit_warning}\033[0m")

        except (KeyboardInterrupt, EOFError):
            exit_msg = SYSTEM.get_text('exit_msg')
            print(f"\n{theme}{exit_msg}{reset}")
            break

def run_batch_mode(inputs: list[str], profile: ProgrammingProfile):
    factory = AnsiFactory(profile)
    theme = profile.get_theme_ansi()
    reset = "\033[0m"
    
    results = [] 
    max_label_len = 0
    
    flat_inputs = []
    for inp in inputs:
        parts = [p.strip() for p in inp.replace(',', ' ').split()]
        flat_inputs.extend(parts)

    for token in flat_inputs:
        result = process_token(token, factory, reset)
        if result:
            p_name, d_name, _, _ = result
            visible_label = f"{p_name} ({d_name})"
            max_label_len = max(max_label_len, len(visible_label))
            results.append(result)

    if not results: return

    print("") 
    for idx, (p_name, d_name, c_inner, blk) in enumerate(results, 1):
        print_result_line(idx, p_name, d_name, c_inner, blk, max_label_len, theme)
    print("") 

def main():
    if os.name == 'nt':
        os.system('')

    parser = AestheticParser(
        description="Color Generator ANSI",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False 
    )
    
    parser.add_argument('-h', '--help', action='help', help=argparse.SUPPRESS)
    parser.add_argument('--pack', default=None, help='Set pack interface and colors')
    parser.add_argument('-r', '--random', nargs='?', const=1, type=int, metavar='N', help='Generate N random colors')
    
    parser.add_argument('--update', action='store_true', help='Check and apply updates')
    parser.add_argument('--version', action='store_true', help='Show version info')

    group = parser.add_mutually_exclusive_group()
    
    for key, profile in TARGET_PROFILES.items():
        group.add_argument(
            *profile.flags, 
            action='store_const', 
            const=key, 
            dest='selected_profile',
            help=SYSTEM.get_text('help_gen_profile', profile.name)
        )

    parser.add_argument('inputs', nargs='*', help='List of colors (Hex or Name)')

    args = parser.parse_args()

    if args.version:
        print(f"CGen v{VERSION}")
        sys.exit(0)
        
    if args.update:
        check_for_updates(silent=False, manual_request=True)

    if not args.update and SYSTEM.get_config_val('check-update', True):
        if sys.stdout.isatty():
            check_for_updates(silent=True, manual_request=False)

    available_packs = SYSTEM.get_available_packs()
    target_pack = 'en' 

    if args.pack:
        target_pack = args.pack
        SYSTEM.save_pack(target_pack)
    elif len(available_packs) == 1:
        target_pack = available_packs[0]
    elif len(available_packs) > 1:
        target_pack = SYSTEM.config.get('pack', 'en')

    SYSTEM.load_pack(target_pack)

    target_id = args.selected_profile if args.selected_profile else SYSTEM.config.get('language', 'python')

    if target_id not in TARGET_PROFILES:
        target_id = 'python'
        
    if args.selected_profile:
        SYSTEM.save_profile(target_id)
        
    profile = TARGET_PROFILES[target_id]

    processed_inputs = args.inputs if args.inputs else []
    limit_warning = None 

    if args.random is not None:
        count = args.random
        limit = SYSTEM.get_config_val('random-limit', 100)
        
        if count > limit:
            SYSTEM.save_random_limit(limit)
            limit_warning = SYSTEM.get_text('security_limit_msg', limit)
            count = limit
            
        rand_colors = [f"#{random.randint(0, 0xFFFFFF):06x}" for _ in range(count)]
        processed_inputs.extend(rand_colors)

    if processed_inputs:
        run_batch_mode(processed_inputs, profile)
        if limit_warning:
            print(f"\033[93m{limit_warning}\033[0m")
    else:
        interactive_mode(profile)

if __name__ == "__main__":
    main()
