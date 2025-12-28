**CGen - ColorGenerator**

CGen is a cross-platform Python utility designed to generate ANSI color escape codes for various programming languages. It allows developers to quickly convert color names or Hex codes into the specific string format required by their language of choice (Python, Java, C++, etc.), complete with a visual preview in the terminal.

**1. FEATURES**

+ Multi-Language Support  : Generates ANSI codes formatted specifically for Python, Java, C++, JavaScript, Bash, Ruby, and Go.
+ Input Flexibility  : Accepts standard color names (e.g., red, azure) and Hex codes (e.g., #FF5733, FF5733, #256, 256).
+ Interactive Mode  : A REPL interface to generate colors continuously without restarting the script.
+ Batch Mode  : Process multiple colors or hex codes directly from the command line arguments.
+ Random Generation  : Generate N random colors for testing or inspiration.
+ Color Preview  : Displays a visual block of the color alongside the generated code.
+ Localization  : Support for interface translation and localized color names (JSON-based).
+ Configuration  : Automatically saves user preferences (last used pack and target profile).

**2. REQUIREMENTS**

+ Python 3.x installed on the system.
+ Terminal with ANSI color support (standard in Linux/macOS, available in Windows 10/11).

**3. INSTALLATION AND SETUP**

[ Method A ] Direct Usage
1. Ensure Python is installed.
2. Download the project files.
3. Run the script via terminal:
   python CGen.py

[ Method B ] Global Path (Windows Optional)
To run the script from any location using the command 'cgen':

1. Locate the folder containing 'cgen.bat' and 'CGen.py'.
2. Copy the full path to this folder.
3. Open Windows Environment Variables.
4. Edit the 'Path' variable in System or User variables.
5. Click 'New' and paste the folder path.
6. Click OK to save.
7. Open a new terminal and type 'cgen' to launch.

**4. USAGE**

CGen can be used in two modes: Interactive (Menu) or Command Line (Batch).

[ 4.1 ] Interactive Mode
If no arguments are provided, the script enters interactive mode.

Command:
python CGen.py

Interface:
- The prompt will show the current target language (e.g., Python Color Mode).
- Type a color name or hex code and press Enter.
- Type 'random [N]' to generate random colors.
- Type 'exit' to quit.

[ 4.2 ] Command Line Mode
Pass flags and inputs directly to generate codes instantly.

Syntax:
python CGen.py [PROFILE_FLAG] [INPUTS...]

Examples:
- Generate code for Red in Python:
  python CGen.py -p red

- Generate code for a Hex value in Java:
  python CGen.py -j #FF5500

- Generate 5 random colors for C++:
  python CGen.py -c -r 5

- Mix inputs (Color names and Hex):
  python CGen.py `--bash` green #000000 white

**5. ARGUMENTS AND FLAGS**

[ Profile Flags ]
Select the target programming language for the output syntax.
```
-p, --python    : Python format (\033[...m)
-j, --java      : Java format (\u001b[...m)
-c, --cpp       : C++ format (\x1b[...m)
-s, --js        : JavaScript format (\u001b[...m)
-b, --bash      : Bash/Shell format (\e[...m)
-rb, --ruby     : Ruby format (\e[...m)
-g, --go        : Golang format (\x1b[...m)
```
[ General Options ]
```
-h, --help      : Show the help menu.
-r, --random N  : Generate N random colors (Default limit: 100).
--pack <code>   : Set the interface language (e.g., --pack es).
```
[ Inputs ]
After flags, you can list any number of color names or hex codes.
Examples: red, blue, #FFFFFF, charcoal.

**6. CONFIGURATION**

The script automatically creates/updates a configuration file located at:
assets/settings.json

Stored Settings:
- pack  : The active interface language code (default: en).
- language  : The last used programming profile (e.g., java).
- random_limit  : The max limit for random generation to prevent overflow.

**7. LOCALIZATION**

CGen supports adding new languages via the 'lang' directory.
Files must be named in the format: color_[CODE].json

Structure of a language file:
```
{
    "palette": {
        "color_name": "#HEXCODE"
    },
    "interface": {
        "string_key": "Translated Text"
    }
}
```
Existing Languages:
- en (English)  : Default
- es (Spanish)
- de (Germany)
- pt (Portuguese)
- ru (Russian)

If a user inputs a color name from a known language that is not currently loaded (e.g., typing 'rojo' while in English mode), the system will attempt to detect the language and suggest the correct language file if available.
