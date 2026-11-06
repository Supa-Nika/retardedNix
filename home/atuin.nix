{ ... }:

# Shared atuin (shell history) setup, imported by both desktop and server.
{
  programs.bash.enable = true;

  programs.atuin = {
    enable = true;
    enableBashIntegration = true;

    # Turn off daemon mode to let the shell log commands directly to SQLite
    daemon.enable = false;

    settings = {
      auto_sync = true;
      sync_frequency = "15m";
      sync_address = "https://api.atuin.sh";
      search_mode = "fuzzy";
      style = "compact";
      enter_accept = false;
    };
  };
}
