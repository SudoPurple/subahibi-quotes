#!/usr/bin/env bash
#
# SubaHibi Terminal Quotes Installer
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
GRAY='\033[0;90m'
NC='\033[0m'

BIN_DIR="$HOME/.local/bin"
DATA_DIR="$HOME/.local/share/subahibi-quotes"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${PURPLE}✦ Subarashiki Hibi Terminal Quotes Installer ✦${NC}\n"

# Check for uninstall flag
if [[ "$1" == "--uninstall" ]]; then
    echo -e "${CYAN}Uninstalling SubaHibi Quotes...${NC}"
    rm -f "$BIN_DIR/subahibi-quote"
    rm -rf "$DATA_DIR"
    echo -e "${GREEN}✓ Removed binaries and data directory.${NC}"
    echo -e "${GRAY}Note: Any hook lines added to ~/.bashrc, ~/.zshrc, or ~/.config/fish/config.fish should be removed manually.${NC}"
    exit 0
fi

# 1. Verify Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Error: python3 is required but not installed.${NC}"
    exit 1
fi

# 2. Create directories
mkdir -p "$BIN_DIR"
mkdir -p "$DATA_DIR"

# 3. Install binary
echo -e "${CYAN}Installing subahibi-quote to $BIN_DIR...${NC}"
cp "$SCRIPT_DIR/subahibi-quote" "$BIN_DIR/subahibi-quote"
chmod +x "$BIN_DIR/subahibi-quote"

# 4. Install extractor
echo -e "${CYAN}Installing extractor engine to $DATA_DIR...${NC}"
cp "$SCRIPT_DIR/extractor.py" "$DATA_DIR/extractor.py"
chmod +x "$DATA_DIR/extractor.py"

# 5. Handle quotes database
if [[ -f "$SCRIPT_DIR/quotes.json" ]]; then
    echo -e "${CYAN}Copying pre-extracted quotes database...${NC}"
    cp "$SCRIPT_DIR/quotes.json" "$DATA_DIR/quotes.json"
elif [[ -f "$SCRIPT_DIR/quotes.json.gz" ]]; then
    echo -e "${CYAN}Decompressing pre-extracted quotes database...${NC}"
    gzip -dc "$SCRIPT_DIR/quotes.json.gz" > "$DATA_DIR/quotes.json"
elif [[ -f "$DATA_DIR/quotes.json" ]]; then
    echo -e "${GREEN}✓ Existing quotes database detected at $DATA_DIR/quotes.json${NC}"
else
    # Search for game files
    POSSIBLE_PATHS=(
        "$HOME/Documents/Wonderful.Everyday.DTRH.Uncensored/Wonderful.Everyday.DTRH.Uncensored"
        "$HOME/Games/Wonderful Everyday"
        "$HOME/.wine/drive_c/Program Files (x86)/Steam/steamapps/common/Wonderful Everyday"
        "$HOME/.local/share/Steam/steamapps/common/Wonderful Everyday"
    )

    GAME_PATH=""
    for p in "${POSSIBLE_PATHS[@]}"; do
        if [[ -f "$p/data01101.arc" ]]; then
            GAME_PATH="$p"
            break
        fi
    done

    if [[ -n "$GAME_PATH" ]]; then
        echo -e "${GREEN}✓ Found SubaHibi game archives at:${NC} $GAME_PATH"
        echo -e "${CYAN}Extracting quotes (takes ~30-40 seconds)...${NC}"
        python3 "$DATA_DIR/extractor.py" "$GAME_PATH" "$DATA_DIR/quotes.json"
    else
        echo -e "${GRAY}No pre-built database or game archives found automatically.${NC}"
        echo -e "${GRAY}You can extract quotes anytime with:${NC}"
        echo -e "  python3 $DATA_DIR/extractor.py /path/to/game/folder"
    fi
fi

# 6. Ensure ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "\n${PURPLE}Notice:${NC} $HOME/.local/bin is not in your current PATH."
    echo -e "Add this to your shell config: ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
fi

# 7. Shell integration hook
CURRENT_SHELL="$(basename "$SHELL")"
echo -e "\n${PURPLE}Shell Integration:${NC}"

# Fish Shell
if command -v fish >/dev/null 2>&1 && [[ -f "$HOME/.config/fish/config.fish" ]]; then
    if grep -q "subahibi-quote" "$HOME/.config/fish/config.fish"; then
        echo -e "${GREEN}✓ Fish hook already present in ~/.config/fish/config.fish${NC}"
    else
        read -p "Add SubaHibi quote greeting to ~/.config/fish/config.fish? [Y/n] " -r REPLY
        REPLY=${REPLY:-Y}
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cat << 'EOF' >> "$HOME/.config/fish/config.fish"

# SubaHibi Terminal Quote Greeting
if status is-interactive
    subahibi-quote
end
EOF
            echo -e "${GREEN}✓ Added to ~/.config/fish/config.fish${NC}"
        fi
    fi
fi

# Zsh Shell
if [[ "$CURRENT_SHELL" == "zsh" ]] && [[ -f "$HOME/.zshrc" ]]; then
    if grep -q "subahibi-quote" "$HOME/.zshrc"; then
        echo -e "${GREEN}✓ Zsh hook already present in ~/.zshrc${NC}"
    else
        read -p "Add SubaHibi quote greeting to ~/.zshrc? [Y/n] " -r REPLY
        REPLY=${REPLY:-Y}
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cat << 'EOF' >> "$HOME/.zshrc"

# SubaHibi Terminal Quote Greeting
if [[ -o interactive ]] && command -v subahibi-quote >/dev/null 2>&1; then
    subahibi-quote
fi
EOF
            echo -e "${GREEN}✓ Added to ~/.zshrc${NC}"
        fi
    fi
fi

# Bash Shell
if [[ "$CURRENT_SHELL" == "bash" ]] && [[ -f "$HOME/.bashrc" ]]; then
    if grep -q "subahibi-quote" "$HOME/.bashrc"; then
        echo -e "${GREEN}✓ Bash hook already present in ~/.bashrc${NC}"
    else
        read -p "Add SubaHibi quote greeting to ~/.bashrc? [Y/n] " -r REPLY
        REPLY=${REPLY:-Y}
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cat << 'EOF' >> "$HOME/.bashrc"

# SubaHibi Terminal Quote Greeting
if [[ $- == *i* ]] && command -v subahibi-quote >/dev/null 2>&1; then
    subahibi-quote
fi
EOF
            echo -e "${GREEN}✓ Added to ~/.bashrc${NC}"
        fi
    fi
fi

echo -e "\n${GREEN}✦ Installation complete! ✦${NC}"
echo -e "Try it out now by running: ${CYAN}subahibi-quote${NC}\n"
EOF
