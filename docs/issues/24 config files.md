# #24 Config files

As an alleycat user I can run `alleycat init`  or perhaps alleycat-init
this will run through a console series of questions that will elicit default values for application settings
e.g.

Your OpenAI API Key (get here) : {paste buffer }
Your preferred model: [gpt4o, gpt4o-mini, ... ] - pick list or enter text
Do you want to create a knowledge base ( you can do this later): {enter name}
Do you want a default persona - pick list [ Johnson, Diderot, bash, ...]  from files listed 
Enter a default folder to look for instruction files: [ folder path]
etc.

These values are stored in the XDG defined config file storage location e.g. ~/.config/alleycat/config.yml - this base folder is defined by $XDG_CONFIG_HOME. or $HOME/.config 

modern best practice is to use the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html), which is widely adopted across Linux distributions and increasingly on macOS.

Recommended Approach (XDG Standard)

	•	Config files: ~/.config/alleycat/settings.json
	•	Data files: ~/.local/share/alleycat/
	•	Cache files: ~/.cache/alleycat/

The [platformdirs](https://pypi.org/project/platformdirs/) Python module provides a cross-platform way to handle configuration, data, cache, and log directories following the XDG Base Directory Specification on Linux/macOS and their equivalents on Windows.

```python
from platformdirs import user_config_dir, user_data_dir, user_cache_dir
import os

app_name = "alleycat"

# Get paths based on XDG standards
config_dir = user_config_dir(app_name)  # ~/.config/myapp/
data_dir = user_data_dir(app_name)      # ~/.local/share/myapp/
cache_dir = user_cache_dir(app_name)    # ~/.cache/myapp/

# Ensure the directories exist
os.makedirs(config_dir, exist_ok=True)

# Path to the config file
config_file = os.path.join(config_dir, "config.yml")

print(f"Config file should be stored at: {config_file}")
```

The Settings object should be serialised to JSON 

Priority for reading settings is

- coded defaults ( lowest)
- config file
- env vars
- command line parameters ( highest )
