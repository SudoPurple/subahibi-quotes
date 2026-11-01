# subahibi-quotes

![Subarashiki Hibi](assets/banner.jpg)

Terminal quote generator and login greeting for *Subarashiki Hibi ~Furenzoku Sonzai~* (*Wonderful Everyday*).

Displays a random quote whenever you open a terminal, with character and chapter attribution. Quotes are parsed directly from the visual novel's scenario files.

```
“The sky didn't care that it was the weekend. It hadn't changed one bit.”
  ― Minakami Yuki (Down the Rabbit-Hole I)
```

## Install

```bash
git clone https://github.com/SudoPurple/subahibi-qoutes.git
cd subahibi-qoutes
./install.sh
```

The installer places `subahibi-quote` in `~/.local/bin/` and sets up the quotes database. It can also add the startup hook to your shell config automatically.

### Manual Shell Setup

If you prefer to set up the startup greeting yourself:

**Fish** (`~/.config/fish/config.fish`):
```fish
function fish_greeting
    if status is-interactive
        subahibi-quote
    end
end
```

**Bash** (`~/.bashrc`):
```bash
if [[ $- == *i* ]] && command -v subahibi-quote >/dev/null 2>&1; then
    subahibi-quote
fi
```

**Zsh** (`~/.zshrc`):
```zsh
if [[ -o interactive ]] && command -v subahibi-quote >/dev/null 2>&1; then
    subahibi-quote
fi
```

## Usage

```bash
# Print a random quote
subahibi-quote

# Filter by character
subahibi-quote -c Yuki
subahibi-quote -c Zakuro
subahibi-quote -c Takuji
subahibi-quote -c Kimika

# Filter by chapter
subahibi-quote --chapter "Insects"
subahibi-quote --chapter "Invention"
subahibi-quote --chapter "Rabbit-Hole"

# Search for a keyword
subahibi-quote --search "Wittgenstein"
subahibi-quote --search "sky"

# Spoken dialogue only vs. narrative monologues
subahibi-quote --dialogue
subahibi-quote --monologue

# Styles
subahibi-quote --style minimal    # Default
subahibi-quote --style card       # Left accent bar
subahibi-quote --style box        # Border box

# Plain text output (useful for scripts, tmux, or status bars)
subahibi-quote --plain

# View all available characters
subahibi-quote --list-characters
```

## Styles

**Minimalist** (Default):
```
“All a woman needs in life are cigarettes, a roof, and a frilly dress, right?”
  ― Minakami Yuki (Down the Rabbit-Hole I)
```

**Card** (`--style card`):
```
▌ “Even if you can't see the light right now, tomorrow might be different.”
▌ ― Takashimadaira Zakuro (Looking-glass Insects)
```

**Box** (`--style box`):
```
╭──────────────────────────────────────────────────────────────────────────╮
│  “The world is everything that is the case.”                             │
│                                                                          │
│                                   ― Ludwig Wittgenstein, [Jabberwocky I] │
╰──────────────────────────────────────────────────────────────────────────╯
```

## Re-extracting from Game Files

A pre-extracted database is included, so having the game installed locally isn't required.

If you want to re-extract quotes yourself (e.g. from patched game files):

```bash
python3 extractor.py /path/to/Wonderful.Everyday.DTRH.Uncensored
```

## License

MIT
