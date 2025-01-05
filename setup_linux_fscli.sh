#!/bin/bash

# Define the directory containing fscli.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create the fscli shell script
echo "Creating fscli shell script..."
cat <<EOL > "$SCRIPT_DIR/fscli"
#!/bin/bash
python3 "$SCRIPT_DIR/fscli.py" "\$@"
EOL

# Make the fscli script executable
echo "Making fscli script executable..."
chmod +x "$SCRIPT_DIR/fscli"

# Add the directory to PATH if not already added
SHELL_CONFIG="$HOME/.bashrc"
if [[ "$SHELL" == *"zsh"* ]]; then
  SHELL_CONFIG="$HOME/.zshrc"
fi

if ! grep -q "$SCRIPT_DIR" "$SHELL_CONFIG"; then
  echo "Adding $SCRIPT_DIR to PATH in $SHELL_CONFIG..."
  echo "export PATH=\"\$PATH:$SCRIPT_DIR\"" >> "$SHELL_CONFIG"
  echo "Sourcing $SHELL_CONFIG to apply the changes..."
  source "$SHELL_CONFIG"
else
  echo "$SCRIPT_DIR is already in PATH."
fi

echo "Setup complete. You can now use 'fscli' command."
